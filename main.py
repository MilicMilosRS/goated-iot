import threading
import time
from settings import load_settings
from components.button import Button
from components.uds import UltrasonicDistanceSensor
from components.door_light import run_door_light
from components.buzzer import run_buzzer
from components.dms import MembraneSwitch
from components.dpir import PassiveInfraredSensor
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
        ds1 = Button(settings['DS1'])
        ds1.start(threads, stop_event)
        dus1 = UltrasonicDistanceSensor(settings['DUS1'])
        dus1.start(threads, stop_event)
        run_door_light(settings['DL'], threads, stop_event)
        run_buzzer(settings['DB'], threads, stop_event)
        dms = MembraneSwitch(settings['DMS'])
        dms.start(threads, stop_event)
        dpir1 = PassiveInfraredSensor(settings['DPIR1'])
        dpir1.start(threads, stop_event)
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nHalting")
        stop_event.set()

        for t in threads:
            t.join()

        print("Halted")
