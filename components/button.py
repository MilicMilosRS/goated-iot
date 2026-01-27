import random
import threading
import time
from mqtt_daemon import data_queue
from components.local_gpio import LocalGPIO

class Button():
    def __init__(self, cfg):
        self.cfg = cfg
    
    def state_changed(self, state):
        data = {
            'sensor': 'Button',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            'value': "Pressed" if state else "Released",
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def start(self, threads: list, stop_event: threading.Event):
        if not self.cfg['simulated']:
            self.GPIO = LocalGPIO()

            #Wait for button press
            #TODO: debounce?
            def loop():
                last = False
                while not stop_event.is_set():
                    val = self.GPIO.read_value(self.cfg['pin'])
                    if val != last:
                        self.state_changed(val)
                    last = val
                    time.sleep(self.cfg['delay'])

            self.GPIO.setup_in_pull_up(self.cfg['pin'])
            t = threading.Thread(target=loop)
            t.start()
            threads.append(t)
        else:
            def loop():
                last = False
                while not stop_event.is_set():
                    val = random.random() < 0.5
                    if val != last:
                        self.state_changed(val)
                        last = val
                    time.sleep(self.cfg['delay'])
            t = threading.Thread(target=loop)
            t.start()
            threads.append(t)