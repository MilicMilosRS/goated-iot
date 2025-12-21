
import threading
from settings import load_settings
from components.ds import run_ds
from components.uds import run_uds
from components.door_light import run_door_light
from components.door_buzzer import run_door_buzzer
import time

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass


if __name__ == "__main__":
    print('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    try:
        run_ds(settings['DS1'], threads, stop_event)
        run_uds(settings['UDS1'], threads, stop_event)
        run_door_light(settings['DL'], threads, stop_event)
        run_door_buzzer(settings['DB'], threads, stop_event)
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            stop_event.set()
