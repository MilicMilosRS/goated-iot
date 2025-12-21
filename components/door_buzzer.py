
from simulators.buzzer import run_buzzer_simulator
import threading
import time

def door_buzzer_callback(state):
    t = time.localtime()
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Door Buzzer")
    status = "TURNED ON" if state else "TURNED OFF"
    print(f"Status: {status}")


def run_door_buzzer(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting Door Buzzer simulation")
            db_thread = threading.Thread(target = run_buzzer_simulator, args=(door_buzzer_callback, stop_event))
            db_thread.start()
            threads.append(db_thread)
            print("Door Buzzer simulation started")
        else:
            pass