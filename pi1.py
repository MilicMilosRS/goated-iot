import argparse
from ast import parse
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

    parser = argparse.ArgumentParser(description="PI1 device.")
    parser.add_argument("-a", "--active", default=True, help="Activate the simulations at startup")
    args = parser.parse_args()

    settings = load_settings("pi1_settings.json")
    mqtt_settings = load_settings("mqtt_settings.json")
    threads = []
    stop_event = threading.Event()

    
    ds1 = Button(settings['DS1'])
    dus1 = UltrasonicDistanceSensor(settings['DUS1'])
    dl = LED(settings['DL'])
    db = Buzzer(settings['DB'])
    dms = MembraneSwitch(settings['DMS'])
    dpir1 = PassiveInfraredSensor(settings['DPIR1'])

    all_sensors = [ds1, dus1, dms, dpir1]

    if args.active == 'false':
        for s in all_sensors:
            s.active = False

    def on_actuator_message(data):
        device = data.get("device")
        state  = data.get("state")

        if device == "DB":
            db.set_state(state)
        elif device == "DL1":
            dl.set_state(state)

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

    ds1.start(threads, stop_event)
    dus1.start(threads, stop_event)
    dms.start(threads, stop_event)
    dpir1.start(threads, stop_event)

    while True:
        #BON - BUZZER ON
        #BOFF - BUZZER OFF
        #LEDON - LED ON
        #LEDOFF - LED OFF
        #END - END PROGRAM
        command = input()

        if command == "DS1":
            c = input()
            if c == "ON":
                ds1.active = True
            elif c == "OFF":
                ds1.active = False
            elif c == "TRUE":
                ds1.simulate_state(True)
            elif c == "FALSE":
                ds1.simulate_state(False)

        if command == "DPIR1":
            c = input()
            if c == "ON":
                dpir1.active = True
            elif c == "OFF":
                dpir1.active = False
            elif c == "TRUE":
                dpir1.simulate_state(True)
            elif c == "FALSE":
                dpir1.simulate_state(False)

        if command == "DUS1":
            c = input()
            if c == "ON":
                dus1.active = True
            elif c == "OFF":
                dus1.active = False
                
        if command == "DMS":
            c = input()
            if c == "ON":
                dms.active = True
            elif c == "OFF":
                dms.active = False
            else:
                dms.simulate_state(c)

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
