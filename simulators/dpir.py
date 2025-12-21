import time
import random

def run_dpir_simulator(
    check_interval,
    motion_probability,
    active_time,
    callback,
    stop_event
):
    """
    Simulatio nof digital PIR motion sensor for doors
    Output:
        1 = motion detected
        0 = no motion
    """
    state = 0

    while not stop_event.is_set():
        time.sleep(check_interval)

        if state == 1:
            continue

        if random.random() < motion_probability:
            state = 1
            callback(state)

            time.sleep(active_time)

            state = 0
            callback(state)
