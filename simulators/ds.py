import time
import random

#Chance for output to be 1
CHANCE = 0.3

def run_ds_simulator(delay, callback, stop_event):
      while not stop_event.is_set():
            time.sleep(delay)
            callback(random.random() < CHANCE)