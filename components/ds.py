from mqtt.mqtt_buffer import push
from mqtt import mqtt, mqtt_buffer
from simulators.ds import run_ds_simulator
import threading
import time

def read_ds(cfg):
    if cfg["simulated"]:
        return run_ds_simulator()
    else:
        return GPIO.input(cfg["pin"])

def run_ds(cfg, threads, stop_event):
    def worker():
        while not stop_event.is_set():
            value = read_ds(cfg)

            push({
                "sensor": "DS",
                "value": int(value),
                "timestamp": time.time(),
                "simulated": cfg["simulated"]
            })

            time.sleep(1)

    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)
