

from simulators.ds import run_ds_simulator
import threading
import time

def ds_callback(state):
    t = time.localtime()
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"DS1")
    status = "Button pressed" if state else "Button not pressed"
    print(f"Status: {status}")


def run_ds(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting DS1 sumilation")
            ds1_thread = threading.Thread(target = run_ds_simulator, args=(2, ds_callback, stop_event))
            ds1_thread.start()
            threads.append(ds1_thread)
            print("DS1 simulation started")
        else:
            pass