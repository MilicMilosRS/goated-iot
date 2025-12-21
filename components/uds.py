

from simulators.uds import run_uds_simulator
import threading
import time

def uds_callback(distance):
    t = time.localtime()
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"UDS1")
    print(f"Status: {distance} cm")


def run_uds(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting UDS1 simulation")
            uds1_thread = threading.Thread(target = run_uds_simulator, args=(settings['delay'], uds_callback, stop_event))
            uds1_thread.start()
            threads.append(uds1_thread)
            print("UDS1 simulation started")
        else:
            pass