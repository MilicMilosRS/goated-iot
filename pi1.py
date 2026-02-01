import threading
from settings import load_settings
from components.button import Button
from components.uds import UltrasonicDistanceSensor
from components.led import LED
from components.buzzer import Buzzer
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

    settings = load_settings("pi1_settings.json")
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

    ds1 = Button(settings['DS1'])
    ds1.start(threads, stop_event)
    dus1 = UltrasonicDistanceSensor(settings['DUS1'])
    dus1.start(threads, stop_event)
    dl = LED(settings['DL'])
    db = Buzzer(settings['DB'])
    dms = MembraneSwitch(settings['DMS'])
    dms.start(threads, stop_event)
    dpir1 = PassiveInfraredSensor(settings['DPIR1'])
    dpir1.start(threads, stop_event)
    while True:
        #BON - BUZZER ON
        #BOFF - BUZZER OFF
        #LEDON - LED ON
        #LEDOFF - LED OFF
        #END - END PROGRAM
        command = input()
        if command == "BON":
            db.set_state(True)
        if command == "BOFF":
            db.set_state(False)
        if command == "LEDON":
            dl.set_state(True)
        if command == "LEDOFF":
            dl.set_state(False)
        if command == "END":
            break

    print("\nHalting")
    stop_event.set()

    for t in threads:
        t.join()

    print("Halted")
