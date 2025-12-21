import threading
import time

from settings import load_settings
from components.ds import run_ds
from components.uds import run_uds
from components.dpir import run_dpir
from components.dms import run_dms

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
        if "DS1" in settings:
            run_ds(settings["DS1"], threads, stop_event)

        if "UDS1" in settings:
            run_uds(settings["UDS1"], threads, stop_event)

        if "DPIR1" in settings:
            run_dpir(settings["DPIR1"], threads, stop_event)

        if "DMS1" in settings:
            run_dms(settings["DMS1"], threads, stop_event)

        print("System running")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nHalting")
        stop_event.set()

        for t in threads:
            t.join()

        print("Halted")
