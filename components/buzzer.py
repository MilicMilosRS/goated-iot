
from components.local_gpio import LocalGPIO
import time
from mqtt_daemon import data_queue

class Buzzer():
    def __init__(self, cfg):
        self.cfg = cfg
        self.buzzing = False
        self.GPIO = LocalGPIO()
    
    def state_changed(self, state):
        data = {
            'sensor': 'Buzzer',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            'value': state,
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def set_state(self, buzzing: bool):
        if self.buzzing == buzzing:
            return
        
        if not self.cfg['simulated']:
            self.GPIO.write_value(self.cfg['pin'], buzzing)
        else:
            print(f"Buzzer turned {"ON" if buzzing else "OFF"}")
        self.state_changed(buzzing)
        self.buzzing = buzzing