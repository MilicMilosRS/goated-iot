import argparse
import threading
from components.dht import DHT
from components.gyro import Gyro
from components.segment_display import SegmentDisplay
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

    parser = argparse.ArgumentParser(description="PI1 device.")
    parser.add_argument("-a", "--active", default=True, help="Activate the simulations at startup")
    args = parser.parse_args()

    settings = load_settings("pi2_settings.json")
    mqtt_settings = load_settings("mqtt_settings.json")
    threads = []
    stop_event = threading.Event()

    ds2 = Button(settings['DS2'])
    dus2 = UltrasonicDistanceSensor(settings['DUS2'])
    dpir2 = PassiveInfraredSensor(settings['DPIR2'])
    sd = SegmentDisplay(settings['4SD'])
    btn = Button(settings['BTN'])
    dht3 = DHT(settings["DHT3"])
    gsg = Gyro(settings["GSG"])

    all_sensors = [ds2, dus2, dpir2, btn, dht3, gsg]

    def on_actuator_message(data):
        device = data.get("device")
        state  = data.get("state")

        if device == "4SD":
            sd.set_state(data.get('text'))

    mqtt_thread = MqttDaemon(
        broker=mqtt_settings['broker'],
        stop_event=stop_event,
        topic=mqtt_settings['topic'],
        subscribe_topic=mqtt_settings['actuator_topic'],
        on_message_callback=on_actuator_message,
        batch_size=10,
        interval=2
    )
    mqtt_thread.start()
    threads.append(mqtt_thread)

    if args.active == 'false':
        for s in all_sensors:
            s.active = False

    ds2.start(threads, stop_event)
    dus2.start(threads, stop_event)
    dpir2.start(threads, stop_event)
    btn.start(threads, stop_event)
    dht3.start(threads, stop_event)
    gsg.start(threads, stop_event)
    while True:
        #END - END PROGRAM
        command = input()

        if command == "DS2":
            c = input()
            if c == "ON":
                ds2.active = True
            elif c == "OFF":
                ds2.active = False
            elif c == "TRUE":
                ds2.simulate_state(True)
            elif c == "FALSE":
                ds2.simulate_state(False)

        if command == "DUS2":
            c = input()
            if c == "ON":
                dus2.active = True
            elif c == "OFF":
                dus2.active = False

        if command == "DPIR2":
            c = input()
            if c == "ON":
                dpir2.active = True
            elif c == "OFF":
                dpir2.active = False
            elif c == "TRUE":
                dpir2.simulate_state(True)
            elif c == "FALSE":
                dpir2.simulate_state(False)

        if command == "BTN":
            c = input()
            if c == "ON":
                btn.active = True
            elif c == "OFF":
                btn.active = False
            elif c == "TRUE":
                btn.simulate_state(True)
            elif c == "FALSE":
                btn.simulate_state(False)
        
        if command == "GSG":
            c = input()
            if c == "ON":
                gsg.active = True
            elif c == "OFF":
                gsg.active = False

        if command == "DHT3":
            c = input()
            if c == "ON":
                dht3.active = True
            elif c == "OFF":
                dht3.active = False

        if command == "END":
            break
        elif command == "4SD":
            msg = input()
            sd.set_state(msg)

    print("\nHalting")
    stop_event.set()

    for t in threads:
        t.join()

    print("Halted")
