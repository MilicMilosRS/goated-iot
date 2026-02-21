
from components.local_gpio import LocalGPIO
import time
from mqtt_daemon import data_queue

class RGBLED():
    def __init__(self, cfg):
        self.cfg = cfg
        self.red_pin = cfg['red_pin']
        self.green_pin = cfg['green_pin']
        self.blue_pin = cfg['blue_pin']
        self.GPIO = LocalGPIO()
        if not cfg['simulated']:
            self.GPIO.setup_in(self.red_pin)
            self.GPIO.setup_in(self.green_pin)
            self.GPIO.setup_in(self.blue_pin)
    
    def state_changed(self, r, g, b):
        data = {
            'sensor': 'RGB LED',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            "fields": ["red", "green", "blue"],
            "red": r,
            "green": g,
            "blue": b,
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def set_state(self, r: bool, g: bool, b: bool):
        if not self.cfg['simulated']:
            self.GPIO.write_value(self.red_pin, r)
            self.GPIO.write_value(self.green_pin, g)
            self.GPIO.write_value(self.blue_pin, b)
        else:
            print(f"RGB LED state: R:{r} G:{g} B:{b}")
        self.state_changed(r, g, b)