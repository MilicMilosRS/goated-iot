from simulators.led import run_led_simulator
import threading
import time

def door_light_callback(state):
    t = time.localtime()
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Door Light")
    status = "ON" if state else "OFF"
    print(f"Status: {status}")


def run_door_light(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting DL simulation")
            dl_thread = threading.Thread(target = run_led_simulator, args=(door_light_callback, stop_event))
            dl_thread.start()
            threads.append(dl_thread)
            print("DL simulation started")
        else:
            pass