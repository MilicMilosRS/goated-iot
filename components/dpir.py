from simulators.dpir import run_dpir_simulator
import threading
import time

def dpir_callback(state):
    t = time.localtime()
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print("DPIR1")
    print("Status:", "MOTION DETECTED" if state else "NO MOTION")

def run_dpir(settings, threads, stop_event):
    if settings["simulated"]:
        print("Starting DPIR1 simulation")

        dpir_thread = threading.Thread(
            target=run_dpir_simulator,
            args=(
                settings["check_interval"],
                settings["motion_probability"],
                settings["active_time"],
                dpir_callback,
                stop_event
            )
        )

        dpir_thread.start()
        threads.append(dpir_thread)

        print("DPIR1 simulation")
    else:
        pass
