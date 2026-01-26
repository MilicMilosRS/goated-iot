import threading
import time
from collections import deque
from settings import load_settings
from components.ds import run_ds
from components.uds import run_uds
from components.door_light import run_door_light
from components.door_buzzer import run_door_buzzer
from components.dms import run_dms
from components.dpir import run_dpir
from mqtt_daemon import MqttDaemon

import time

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except ImportError:
    GPIO = None


if __name__ == "__main__":
    print("Starting app")

    settings = load_settings()
    threads = []
    stop_event = threading.Event()

    mqtt_thread = MqttDaemon(
        broker=settings['mqtt']['broker'],
        stop_event=stop_event,
        topic=settings['mqtt']['topic'],
        batch_size=10,
        interval=2
    )

    mqtt_thread.start()
    threads.append(mqtt_thread)

    try:
        run_ds(settings['DS1'], threads, stop_event, "PI1")
        run_uds(settings['UDS1'], threads, stop_event)
        run_door_light(settings['DL'], threads, stop_event)
        run_door_buzzer(settings['DB'], threads, stop_event)
        run_dms(settings['DMS1'], threads, stop_event)
        run_dpir(settings['DPIR1'], threads, stop_event)
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nHalting")
        stop_event.set()

        for t in threads:
            t.join()

        print("Halted")
