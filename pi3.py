import argparse
import threading
from components.dht import DHT
from components.gyro import Gyro
from components.ir_receiver import IRReceiver
from components.lcd import LCD
from components.rgb_led import RGBLED
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
    
    settings = load_settings("pi3_settings.json")
    mqtt_settings = load_settings("mqtt_settings.json")
    threads = []
    stop_event = threading.Event()

    dht1 = DHT(settings["DHT1"])
    dht2 = DHT(settings["DHT2"])
    ir = IRReceiver(settings["IR"])
    brgb = RGBLED(settings["BRGB"])
    lcd = LCD(settings["LCD"])
    dpir3 = PassiveInfraredSensor(settings['DPIR3'])

    all_sensors = [dht1, dht2, ir, dpir3]

    def on_actuator_message(data):
        device = data.get("device")
        state  = data.get("state")

        if device == "LCD":
            lcd.set_state(data.get("text"))
        elif device == "BRGB":
            brgb.set_state(data.get('r'), data.get('g'), data.get('b'))

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

    dht1.start(threads, stop_event)
    dht2.start(threads, stop_event)
    ir.start(threads, stop_event)
    dpir3.start(threads, stop_event)

    while True:
        #END - END PROGRAM
        command = input()

        if command == "DHT1":
            c = input()
            if c == "ON":
                dht1.active = True
            elif c == "OFF":
                dht1.active = False

        if command == "DHT2":
            c = input()
            if c == "ON":
                dht2.active = True
            elif c == "OFF":
                dht2.active = False

        if command == "IR":
            c = input()
            if c == "ON":
                ir.active = True
            elif c == "OFF":
                ir.active = False

        if command == "DPIR3":
            c = input()
            if c == "ON":
                dpir3.active = True
            elif c == "OFF":
                dpir3.active = False

        if command == "END":
            break

    print("\nHalting")
    stop_event.set()

    for t in threads:
        t.join()

    print("Halted")
