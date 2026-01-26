from simulators.ds import run_ds_simulator
import threading
import time
from mqtt_daemon import data_queue

def ds_callback(pi, simulated, state):
    # Point(data["sensor"])
    #     .tag("pi", data["pi"])
    #     .tag("simulated", data["simulated"])
    #     .field("value", data["value"])
    #     .time(data["timestamp"])
    data = {
         'sensor': 'door sensor',
         'pi': pi,
         'simulated': simulated,
         'value': state,
         'timestamp': time.time_ns()
    }
    data_queue.put(data)


def run_ds(settings, threads, stop_event, pi):
        if settings['simulated']:
            print("Starting DS1 sumilation")
            ds1_thread = threading.Thread(target = run_ds_simulator, args=(2, ds_callback, stop_event, pi))
            ds1_thread.start()
            threads.append(ds1_thread)
            print("DS1 simulation started")
        else:
            pass