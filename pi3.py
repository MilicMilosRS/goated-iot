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

    settings = load_settings("pi3_settings.json")
    mqtt_settings = load_settings("mqtt_settings.json")
    threads = []
    stop_event = threading.Event()

    mqtt_thread = MqttDaemon(
        broker=mqtt_settings['broker'],
        stop_event=stop_event,
        topic=mqtt_settings['topic'],
        batch_size=10,
        interval=2
    )

    mqtt_thread.start()
    threads.append(mqtt_thread)

    dht1 = DHT(settings["DHT1"])
    dht2 = DHT(settings["DHT2"])
    ir = IRReceiver(settings["IR"])
    brgb = RGBLED(settings["BRGB"])
    lcd = LCD(settings["LCD"])
    dpir3 = PassiveInfraredSensor(settings['DPIR3'])

    dht1.start(threads, stop_event)
    dht2.start(threads, stop_event)
    ir.start(threads, stop_event)
    dpir3.start(threads, stop_event)

    while True:
        #BRGB1 - All 1
        #BRGB2 - Red
        #BRGB3 - whatever
        #BRGB4 - Off
        #LCD - show message
        #END - END PROGRAM
        command = input()
        if command == "END":
            break
        elif command == "BRGB1":
            brgb.set_state(True, True, True)
        elif command == "BRGB2":
            brgb.set_state(True, False, False)
        elif command == "BRGB3":
            brgb.set_state(True, False, True)
        elif command == "BRGB4":
            brgb.set_state(False, False, False)
        elif command == "LCD":
            msg = input()
            lcd.set_state(msg)

    print("\nHalting")
    stop_event.set()

    for t in threads:
        t.join()

    print("Halted")
