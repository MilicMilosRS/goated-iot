

import random
from components.local_gpio import LocalGPIO
import threading
import time
from mqtt_daemon import data_queue

class UltrasonicDistanceSensor():
    def __init__(self, cfg):
        self.cfg = cfg
    
    def state_changed(self, distance):
        data = {
            'sensor': 'Ultrasonic sensor',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            'value': distance,
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def start(self, threads: list, stop_event: threading.Event):
        if not self.cfg['simulated']:
            self.GPIO = LocalGPIO()
            
            ECHO_PIN = self.cfg['echo_pin']
            TRIG_PIN = self.cfg['trig_pin']

            self.GPIO.setup_out(TRIG_PIN)
            self.GPIO.setup_in(ECHO_PIN)

            def get_distance():
                self.GPIO.write_value(TRIG_PIN, False)
                time.sleep(0.2)
                self.GPIO.write_value(TRIG_PIN, True)
                time.sleep(0.00001)
                self.GPIO.write_value(TRIG_PIN, False)
                pulse_start_time = time.time()
                pulse_end_time = time.time()

                max_iter = 100

                iter = 0
                while self.GPIO.read_value(ECHO_PIN) == 0:
                    if iter > max_iter:
                        return None
                    pulse_start_time = time.time()
                    iter += 1

                iter = 0
                while self.GPIO.read_value(ECHO_PIN) == 1:
                    if iter > max_iter:
                        return None
                    pulse_end_time = time.time()
                    iter += 1

                pulse_duration = pulse_end_time - pulse_start_time
                distance = (pulse_duration * 34300)/2
                return distance
            
            def run():
                while not stop_event.is_set():
                    time.sleep(self.cfg['delay'])
                    distance = get_distance()
                    if distance is not None:
                        self.state_changed(distance)
            
            t = threading.Thread(target=run)
            t.start()
            threads.append(t)
        else:
            def run():
                while not stop_event.is_set():
                    time.sleep(self.cfg['delay'])
                    self.state_changed(random.random() * 20)
            t = threading.Thread(target=run)
            t.start()
            threads.append(t)