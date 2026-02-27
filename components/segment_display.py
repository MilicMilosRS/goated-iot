from components.local_gpio import LocalGPIO
import time
from mqtt_daemon import data_queue

# segments =  (11,4,23,8,7,10,18,25)
# digits = (22,27,17,24)

num = {' ':(0,0,0,0,0,0,0),
    '0':(1,1,1,1,1,1,0),
    '1':(0,1,1,0,0,0,0),
    '2':(1,1,0,1,1,0,1),
    '3':(1,1,1,1,0,0,1),
    '4':(0,1,1,0,0,1,1),
    '5':(1,0,1,1,0,1,1),
    '6':(1,0,1,1,1,1,1),
    '7':(1,1,1,0,0,0,0),
    '8':(1,1,1,1,1,1,1),
    '9':(1,1,1,1,0,1,1)}

class SegmentDisplay():
    def __init__(self, cfg):
        self.cfg = cfg
        self.segments = cfg['segments']
        self.pins = cfg['pins']

        self.GPIO = LocalGPIO()
        if not cfg['simulated']:
            for seg in self.segments:
                self.GPIO.setup_out(seg)
            for pin in self.pins:
                self.GPIO.setup_out(pin)

    def state_changed(self, state):
        data = {
            'sensor': '4 Digit 7 Segment Display',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            'value': state,
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def set_state(self, s: str):
        if not self.cfg['simulated']:
            for digit in range(4):
                for loop in range(0,7):
                    self.GPIO.output(self.segments[loop], num[s[digit]][loop])
                    if (int(time.ctime()[18:19])%2 == 0) and (digit == 1):
                        self.GPIO.output(25, 1)
                    else:
                        self.GPIO.output(25, 0)
                self.GPIO.output(self.digits[digit], 0)
                time.sleep(0.001)
                self.GPIO.output(self.digits[digit], 1)
        else:
            print(f"4 Digit 7 Segment displays says {s}")
        self.state_changed(s)