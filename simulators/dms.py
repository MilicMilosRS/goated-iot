import time
import random

def run_dms_simulator(
    check_interval,
    open_probability,
    callback,
    stop_event
):
    """
    Simulates a magnetic door switch (reed switch)

    0 = door closed
    1 = door open
    """

    state = 0 

    while not stop_event.is_set():
        time.sleep(check_interval)

        if random.random() < open_probability:
            state = 1 - state
            callback(state)
