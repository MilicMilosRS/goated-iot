import json
import math
import time
import logging
import threading
from collections import deque
from queue import Queue, Empty
import paho.mqtt.client as mqtt
import influxDB

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

MQTT_BROKER     = "mosquitto"
MQTT_PORT       = 1883
TOPIC_SENSORS   = "iot/sensors"
TOPIC_ACTUATORS = "iot/actuators"
TOPIC_NOTIFY    = "iot/notifications"

CORRECT_PIN           = "1312"
DOOR_OPEN_THRESHOLD   = 5.0
ARM_DELAY             = 10.0
DL1_ON_DURATION       = 10.0
DISTANCE_WINDOW       = 5.0
GSG_ACCEL_THRESHOLD   = 2.5
GSG_GYRO_THRESHOLD    = 150.0
LCD_ROTATION_INTERVAL = 5.0

TIMER_BLINK_INTERVAL  = 0.5
TIMER_BTN_ADD_DEFAULT = 30

IR_COLOR_MAP: dict[str, tuple[bool, bool, bool]] = {
    "1": (True,  True,  True),
    "2": (True,  False, False),
    "3": (False, True,  False),
    "4": (False, False, True),
    "5": (True,  True,  False),
    "6": (False, True,  True),
    "7": (True,  False, True),
    "8": (False, False, False),
}

_sse_clients: list[Queue] = []
_sse_lock = threading.Lock()

#Register SSE client
def sse_register() -> Queue:
    q: Queue = Queue(maxsize=100)
    with _sse_lock:
        _sse_clients.append(q)
    return q


def sse_unregister(q: Queue):
    with _sse_lock:
        try:
            _sse_clients.remove(q)
        except ValueError:
            pass

#Send payload to all SSE clients
def _broadcast(payload: dict):
    with _sse_lock:
        for q in _sse_clients:
            try:
                q.put_nowait(payload)
            except Exception:
                pass


class KitchenTimer:
    def __init__(self):
        self._lock = threading.Lock()
        self._remaining: float = 0.0
        self._state = "IDLE" # IDLE or RUNNING or EXPIRED
        self._tick_thread: threading.Thread | None = None
        self._blink_thread: threading.Thread | None = None
        self._stop_tick = threading.Event()
        self._stop_blink = threading.Event()
        self.btn_add_seconds = TIMER_BTN_ADD_DEFAULT
        self.mqtt_client = None

    def set_timer(self, seconds: int):
        self._stop_all()
        with self._lock:
            self._remaining = max(0, int(seconds))
            self._state = "RUNNING" if self._remaining > 0 else "IDLE"
        if self._state == "RUNNING":
            self._push_display()
            self._start_tick()
        _broadcast(self._status_payload())
        log.info("Timer set to %d s", seconds)

    def btn_pressed(self):
        with self._lock:
            st = self._state
        if st == "RUNNING":
            self.add_seconds(self.btn_add_seconds)
        elif st == "EXPIRED":
            self.stop_blink()

    def add_seconds(self, n: int):
        with self._lock:
            if self._state == "EXPIRED":
                return
            self._remaining += n
            if self._state == "IDLE" and self._remaining > 0:
                self._state = "RUNNING"
        if self._state == "RUNNING":
            self._push_display()
            if self._tick_thread is None or not self._tick_thread.is_alive():
                self._start_tick()
        _broadcast(self._status_payload())
        log.info("Timer +%d s → %.0f s remaining", n, self._remaining)

    def stop_blink(self):
        self._stop_blink.set()
        with self._lock:
            self._state = "IDLE"
        self._send_4sd("    ")
        _broadcast(self._status_payload())
        log.info("Timer blink stopped")

    def cancel(self):
        self._stop_all()
        with self._lock:
            self._remaining = 0
            self._state = "IDLE"
        self._send_4sd("    ")
        _broadcast(self._status_payload())

    def _start_tick(self):
        self._stop_tick.clear()
        self._tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._tick_thread.start()

    def _tick_loop(self):
        while not self._stop_tick.is_set():
            time.sleep(1.0)
            with self._lock:
                if self._state != "RUNNING":
                    break
                self._remaining -= 1.0
                remaining = self._remaining
            self._push_display()
            if remaining <= 0:
                self._expire()
                break

    def _expire(self):
        with self._lock:
            self._state = "EXPIRED"
        log.info("Timer EXPIRED")
        _broadcast(self._status_payload())
        self._start_blink()

    def _start_blink(self):
        self._stop_blink.clear()
        self._blink_thread = threading.Thread(target=self._blink_loop, daemon=True)
        self._blink_thread.start()

    def _blink_loop(self):
        visible = True
        while not self._stop_blink.is_set():
            self._send_4sd("0000" if visible else "     ")
            visible = not visible
            time.sleep(TIMER_BLINK_INTERVAL)

    def _push_display(self):
        with self._lock:
            rem = max(0, int(self._remaining))
        self._send_4sd(str(rem).rjust(4))

    def _send_4sd(self, text: str):
        if self.mqtt_client:
            payload = {"device": "4SD", "state": True,
                       "text": text, "timestamp": time.time_ns()}
            self.mqtt_client.publish(TOPIC_ACTUATORS, json.dumps(payload))

    def _stop_all(self):
        self._stop_tick.set()
        self._stop_blink.set()

    def _status_payload(self) -> dict:
        with self._lock:
            return {
                "event": "TIMER_STATUS",
                "state": self._state,
                "remaining": max(0, int(self._remaining)),
                "btn_add_sec": self.btn_add_seconds,
                "timestamp": time.time_ns(),
            }

    @property
    def status(self) -> dict:
        return self._status_payload()


class BRGBController:

    def __init__(self):
        self.r     = False
        self.g     = False
        self.b     = False
        self._lock = threading.Lock()
        self.mqtt_client: mqtt.Client | None = None

    def set_color(self, r: bool, g: bool, b: bool, power: bool | None = None):
        with self._lock:
            self.r = r
            self.g = g
            self.b = b
        self._push()
        _broadcast(self._status_payload())

    def handle_ir(self, code: str):
        """Map an IR remote keycode to a BRGB action."""
        action = IR_COLOR_MAP.get(code)
        if action is None:
            log.debug("IR code not mapped: %s", code)
            return
        r, g, b = action
        self.set_color(r, g, b)
        log.info("IR %s -> BRGB r=%s g=%s b=%s", code, r, g, b)

    def _push(self):
        if self.mqtt_client:
            payload = {
                "device": "BRGB",
                "r": self.r, "g": self.g, "b": self.b,
                "timestamp": time.time_ns(),
            }
            self.mqtt_client.publish(TOPIC_ACTUATORS, json.dumps(payload))

    def _status_payload(self) -> dict:
        with self._lock:
            return {
                "event": "BRGB_STATUS",
                "r": self.r, "g": self.g, "b": self.b,
                "timestamp": time.time_ns(),
            }

    @property
    def status(self) -> dict:
        return self._status_payload()


class AlarmSystem:
    def __init__(self):
        self.alarm_active = False
        self._alarm_lock = threading.Lock()
        self._alarm_reasons = []
        self.security_armed = False
        self._arm_timer: threading.Timer | None = None
        self._door_timers: dict[str, threading.Timer] = {}
        self._light_timer: threading.Timer | None = None
        self._distance_history: dict[str, deque] = {
            "DUS1": deque(maxlen=50),
            "DUS2": deque(maxlen=50),
            "DUS3": deque(maxlen=50),
        }
        self.person_count = 0
        self._person_lock = threading.Lock()
        self._dms_buffer: deque[str] = deque(maxlen=4)
        self._dht_readings: dict[str, dict] = {}
        self._dht_lock = threading.Lock()
        self._dht_devices: list[str] = []
        self._dht_index  = 0
        self._lcd_timer: threading.Timer | None = None
        self.mqtt_client: mqtt.Client | None = None

    def _publish(self, topic: str, payload: dict):
        if self.mqtt_client:
            self.mqtt_client.publish(topic, json.dumps(payload))
            log.info("Published → %s : %s", topic, payload)

    def _actuator(self, device: str, state: bool, duration: float | None = None, **extra):
        payload = {"device": device, "state": state, "timestamp": time.time_ns(), **extra}
        if duration:
            payload["duration"] = duration
        self._publish(TOPIC_ACTUATORS, payload)

    def _notify(self, event: str, **kwargs):
        payload = {"event": event, "timestamp": time.time_ns(), **kwargs}
        self._publish(TOPIC_NOTIFY, payload)
        _broadcast(payload)

    def activate_alarm(self, reason: str):
        with self._alarm_lock:
            if self.alarm_active:
                return
            self.alarm_active = True
        log.warning("ALARM ACTIVATED – %s", reason)
        self._actuator("DB", True)
        self._notify("ALARM_ON", reason=reason, person_count=self.person_count)
        self._write_alarm_event("ALARM_ON", reason)

    def deactivate_alarm(self, source: str):
        with self._alarm_lock:
            if not self.alarm_active:
                return
            self.alarm_active = False
        log.info("ALARM DEACTIVATED – %s", source)
        self._actuator("DB", False)
        self._notify("ALARM_OFF", source=source)
        self._write_alarm_event("ALARM_OFF", source)
        self.security_armed = False
        self._cancel_timer(self._arm_timer)

    def _write_alarm_event(self, event: str, detail: str):
        try:
            influxDB.write_alarm_event({"event": event, "detail": detail,
                                        "timestamp": time.time_ns()})
        except Exception as e:
            log.error("InfluxDB write failed: %s", e)

    def handle_pin(self, pin: str, source: str = "DMS"):
        if pin != CORRECT_PIN:
            log.warning("Wrong PIN on %s", source)
            self._notify("PIN_WRONG", source=source)
            return
        if self.alarm_active:
            self.deactivate_alarm(source=source)
            return
        if self.security_armed:
            self.security_armed = False
            self._cancel_timer(self._arm_timer)
            log.info("Security DISARMED via %s", source)
            self._notify("SECURITY_DISARMED", source=source)
            return
        log.info("Correct PIN – arming in %.0f s", ARM_DELAY)
        self._notify("SECURITY_ARMING", delay=ARM_DELAY)
        self._cancel_timer(self._arm_timer)
        self._arm_timer = threading.Timer(ARM_DELAY, self._do_arm)
        self._arm_timer.daemon = True
        self._arm_timer.start()

    def _do_arm(self):
        self.security_armed = True
        log.info("Security system ARMED")
        self._notify("SECURITY_ARMED")

    def handle_pir(self, device: str, value: bool):
        if not value:
            return
        with self._person_lock:
            count = self.person_count
        if count == 0:
            self.activate_alarm(reason=f"Motion detected by {device} but building is empty")
            
        if device == "DPIR1":
            self._cancel_timer(self._light_timer)
            self._actuator("DL1", True, duration=DL1_ON_DURATION)
            self._light_timer = threading.Timer(DL1_ON_DURATION,
                                                lambda: self._actuator("DL1", False))
            self._light_timer.daemon = True
            self._light_timer.start()

        dus_map = {"DPIR1": "DUS1", "DPIR2": "DUS2"}
        dus = dus_map.get(device)
        if dus:
            direction = self._determine_direction(dus)
            if direction == "ENTRY":
                with self._person_lock:
                    self.person_count += 1
                self._notify("PERSON_ENTRY", device=device, person_count=self.person_count)
            elif direction == "EXIT":
                with self._person_lock:
                    self.person_count = max(0, self.person_count - 1)
                self._notify("PERSON_EXIT", device=device, person_count=self.person_count)

    def handle_ultrasonic(self, device: str, value: float):
        if device in self._distance_history:
            self._distance_history[device].append((time.time(), value))

    def handle_door(self, device: str, value: bool):
        if value:
            if device not in self._door_timers or not self._door_timers[device].is_alive():
                t = threading.Timer(DOOR_OPEN_THRESHOLD, self._door_open_alarm, args=(device,))
                t.daemon = True
                t.start()
                self._door_timers[device] = t
            if self.security_armed:
                self.activate_alarm(reason=f"Security breach – {device} opened while armed")
        else:
            self._cancel_timer(self._door_timers.pop(device, None))
            if not self.security_armed:
                self.deactivate_alarm(f"{device} iskljucen")

    def _door_open_alarm(self, device: str):
        self.activate_alarm(reason=f"{device} ukljucen >{DOOR_OPEN_THRESHOLD:.0f}s")

    def handle_dms(self, value: str):
        self._dms_buffer.append(value)
        if len(self._dms_buffer) == 4:
            pin = "".join(self._dms_buffer)
            self._dms_buffer.clear()
            self.handle_pin(pin=pin, source="DMS")

    def handle_gsg(self, packet: dict):
        try:
            ax, ay, az = packet["accel_x"], packet["accel_y"], packet["accel_z"]
            gx, gy, gz = packet["gyro_x"],  packet["gyro_y"],  packet["gyro_z"]
        except KeyError as e:
            log.warning("GSG missing field: %s", e)
            return
        accel_magnitude = math.sqrt(ax**2 + ay**2 + az**2)
        gyro_magnitude  = math.sqrt(gx**2 + gy**2 + gz**2)
        accel_deviation = abs(accel_magnitude - 1.0)
        if accel_deviation > GSG_ACCEL_THRESHOLD or gyro_magnitude > GSG_GYRO_THRESHOLD:
            self.activate_alarm(
                reason=f"Naglo kretanje ziroskopa (accel_dev={accel_deviation:.2f}g, gyro={gyro_magnitude:.1f}/s)")

    def handle_dht(self, device: str, packet: dict):
        temperature = packet.get("temperature")
        humidity    = packet.get("humidity")
        if temperature is None or humidity is None:
            return
        with self._dht_lock:
            self._dht_readings[device] = {"temperature": temperature, "humidity": humidity}
            if device not in self._dht_devices:
                self._dht_devices.append(device)
        if self._lcd_timer is None or not self._lcd_timer.is_alive():
            self._push_to_lcd(device, temperature, humidity)
            self._schedule_lcd_rotation()

    def _schedule_lcd_rotation(self):
        self._lcd_timer = threading.Timer(LCD_ROTATION_INTERVAL, self._rotate_lcd)
        self._lcd_timer.daemon = True
        self._lcd_timer.start()

    def _rotate_lcd(self):
        with self._dht_lock:
            if not self._dht_devices:
                return
            self._dht_index = (self._dht_index + 1) % len(self._dht_devices)
            device  = self._dht_devices[self._dht_index]
            reading = self._dht_readings.get(device)
        if reading:
            self._push_to_lcd(device, reading["temperature"], reading["humidity"])
        self._schedule_lcd_rotation()

    def _push_to_lcd(self, device: str, temperature: float, humidity: float):
        self._actuator("LCD", state=True,
                       text=f"{device}  T:{temperature:.1f}C  H:{humidity:.1f}%")

    def _determine_direction(self, dus: str) -> str | None:
        history = self._distance_history.get(dus)
        if not history:
            return None
        cutoff = time.time() - DISTANCE_WINDOW
        recent = [(t, d) for t, d in history if t >= cutoff]
        if len(recent) < 2:
            return None
        mid = len(recent) // 2
        first_avg  = sum(d for _, d in recent[:mid]) / mid
        second_avg = sum(d for _, d in recent[mid:]) / (len(recent) - mid)
        if second_avg < first_avg:
            return "ENTRY"
        elif second_avg > first_avg:
            return "EXIT"
        return None

    @staticmethod
    def _cancel_timer(t: threading.Timer | None):
        if t and t.is_alive():
            t.cancel()


alarm_system   = AlarmSystem()
kitchen_timer  = KitchenTimer()
brgb           = BRGBController()


def on_connect(client: mqtt.Client, userdata, flags, rc):
    if rc == 0:
        log.info("MQTT connected")
        client.subscribe(TOPIC_SENSORS)
    else:
        log.error("MQTT connection failed, rc=%d", rc)


SENSOR_HANDLERS = {
    "DPIR1": lambda pkt: alarm_system.handle_pir("DPIR1", pkt["value"]),
    "DPIR2": lambda pkt: alarm_system.handle_pir("DPIR2", pkt["value"]),
    "DPIR3": lambda pkt: alarm_system.handle_pir("DPIR3", pkt["value"]),
    "DUS1":  lambda pkt: alarm_system.handle_ultrasonic("DUS1", pkt["value"]),
    "DUS2":  lambda pkt: alarm_system.handle_ultrasonic("DUS2", pkt["value"]),
    "DUS3":  lambda pkt: alarm_system.handle_ultrasonic("DUS3", pkt["value"]),
    "DS1":   lambda pkt: alarm_system.handle_door("DS1", pkt["value"]),
    "DS2":   lambda pkt: alarm_system.handle_door("DS2", pkt["value"]),
    "DMS":   lambda pkt: alarm_system.handle_dms(pkt["value"]),
    "GSG":   lambda pkt: alarm_system.handle_gsg(pkt),
    "DHT1":  lambda pkt: alarm_system.handle_dht("DHT1", pkt),
    "DHT2":  lambda pkt: alarm_system.handle_dht("DHT2", pkt),
    "DHT3":  lambda pkt: alarm_system.handle_dht("DHT3", pkt),
    "BTN":   lambda pkt: kitchen_timer.btn_pressed() if pkt.get("value") else None,
    "IR1":   lambda pkt: brgb.handle_ir(pkt.get("button_name", "")),
}


def on_message(client: mqtt.Client, userdata, msg):
    try:
        raw     = json.loads(msg.payload.decode())
        packets = raw if isinstance(raw, list) else [raw]
        influxDB.write_sensor_data(packets)
        for packet in packets:
            device = packet.get("sensor_device")
            log.debug("Received from %s", device)

            _broadcast({"event": "SENSOR_DATA", **packet})

            handler = SENSOR_HANDLERS.get(device)
            if handler:
                handler(packet)
            else:
                log.warning("No handler for device: %s", device)
    except Exception as e:
        log.error("Error processing MQTT message: %s", e)


def start_mqtt():
    client = mqtt.Client(client_id="flask_alarm_server", clean_session=True)
    client.on_connect = on_connect
    client.on_message = on_message
    client.enable_logger(log)
    alarm_system.mqtt_client  = client
    kitchen_timer.mqtt_client = client
    brgb.mqtt_client          = client
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            break
        except Exception as e:
            log.warning("MQTT connect failed: %s – retrying in 2 s", e)
            time.sleep(2)
    client.loop_forever()