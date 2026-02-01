import threading
from components.dht import DHT
from components.gyro import Gyro
from settings import load_settings
from components.button import Button
from components.uds import UltrasonicDistanceSensor
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

    settings = load_settings("pi2_settings.json")
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

    ds2 = Button(settings['DS2'])
    ds2.start(threads, stop_event)
    dus2 = UltrasonicDistanceSensor(settings['DUS2'])
    dus2.start(threads, stop_event)
    dpir2 = PassiveInfraredSensor(settings['DPIR2'])
    dpir2.start(threads, stop_event)
    btn = Button(settings['BTN'])
    btn.start(threads, stop_event)
    dht3 = DHT(settings["DHT3"])
    dht3.start(threads, stop_event)
    gsg = Gyro(settings["GSG"])
    gsg.start(threads, stop_event)
    while True:
        #END - END PROGRAM
        command = input()
        if command == "END":
            break

    print("\nHalting")
    stop_event.set()

    for t in threads:
        t.join()

    print("Halted")
