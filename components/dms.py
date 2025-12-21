import threading
from simulators.dms import run_dms_simulator
import time

def dms_callback(state):
    t = time.localtime()
    print("=" * 20)
    print("DMS1")
    print("Door:", "OPEN" if state else "CLOSED")

def run_dms(settings, threads, stop_event):
    if settings["simulated"]:
        print("Starting DMS1 simulation")

        t = threading.Thread(
            target=run_dms_simulator,
            args=(
                settings["check_interval"],
                settings["open_probability"],
                dms_callback,
                stop_event
            ),
            daemon=True
        )

        t.start()
        threads.append(t)

        print("DMS1 simulation started")

    else:
        pass
