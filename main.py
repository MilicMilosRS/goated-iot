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

    try:
        run_ds(settings['DS1'], threads, stop_event)
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
