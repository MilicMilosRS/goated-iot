import time
import random

def run_uds_simulator(delay, callback, stop_event):
      while not stop_event.is_set():
            time.sleep(delay)
            callback(random.random() * 20)