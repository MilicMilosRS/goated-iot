import random
import threading
import time
from mqtt_daemon import data_queue
from components.local_gpio import LocalGPIO

class PassiveInfraredSensor():
    def __init__(self, cfg):
        self.cfg = cfg
    
    def state_changed(self, state: bool):
        data = {
            'sensor': 'Motion sensor',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            'value': "Motion detected" if state else "Motion stopped",
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def start(self, threads: list, stop_event: threading.Event):
        if not self.cfg['simulated']:
            self.GPIO = LocalGPIO()
            
            self.GPIO.add_event_detect(self.cfg['pin'], "RISING", callback=lambda ch: self.state_changed(True))
            self.GPIO.add_event_detect(self.cfg['pin'], "FALLING", callback=lambda ch: self.state_changed(False))

            def run():
                while not stop_event.is_set():
                    time.sleep(0.2)

            t = threading.Thread(target=run)
            t.start()
            threads.append(t)

        else:
            def run():
                state = 0
                while not stop_event.is_set():
                    time.sleep(self.cfg['check_interval'])

                    if state == 1:
                        continue

                    if random.random() < self.cfg['motion_probability']:
                        state = 1
                        self.state_changed(True)

                        time.sleep(self.cfg['active_time'])

                        state = 0
                        self.state_changed(False)
            t = threading.Thread(target=run)
            t.start()
            threads.append(t)