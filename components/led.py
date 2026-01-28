
from components.local_gpio import LocalGPIO
import time
from mqtt_daemon import data_queue

class LED():
    def __init__(self, cfg):
        self.cfg = cfg
        self.state = False
        self.GPIO = LocalGPIO()
    
    def state_changed(self, state):
        data = {
            'sensor': 'LED',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            'value': "TURNED ON" if state else "TURNED OFF",
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def set_state(self, state: bool):
        if self.state == state:
            return
        
        if not self.cfg['simulated']:
            self.GPIO.write_value(self.cfg['pin'], state)
        else:
            print(f"LED turned {"ON" if state else "OFF"}")
        self.state_changed(state)
        self.state = state