import random
import threading
from components.local_gpio import LocalGPIO
import time
from mqtt_daemon import data_queue

class MembraneSwitch():
    def __init__(self, cfg):
        self.cfg = cfg

    def state_changed(self, character):
        data = {
            'sensor': 'Membrane switch',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            'value': character,
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def start(self, threads: list, stop_event: threading.Event):
        if not self.cfg['simulated']:
            R1 = self.cfg['pins'][0]
            R2 = self.cfg['pins'][1]
            R3 = self.cfg['pins'][2]
            R4 = self.cfg['pins'][3]

            C1 = self.cfg['pins'][4]
            C2 = self.cfg['pins'][5]
            C3 = self.cfg['pins'][6]
            C4 = self.cfg['pins'][7]

            # Initialize the GPIO pins
            GPIO = LocalGPIO()

            GPIO.setup_out(R1)
            GPIO.setup_out(R2)
            GPIO.setup_out(R3)
            GPIO.setup_out(R4)

            # Make sure to configure the input pins to use the internal pull-down resistors

            GPIO.setup_in_pull_down(C1)
            GPIO.setup_in_pull_down(C2)
            GPIO.setup_in_pull_down(C3)
            GPIO.setup_in_pull_down(C4)

            # The readLine function implements the procedure discussed in the article
            # It sends out a single pulse to one of the rows of the keypad
            # and then checks each column for changes
            # If it detects a change, the user pressed the button that connects the given line
            # to the detected column

            self.last_keys = set()
            self.current_keys = set()

            def readLine(line, characters):
                GPIO.output(line, GPIO.HIGH)
                if(GPIO.read_value(C1) == 1):
                    self.current_keys.add(characters[0])
                if(GPIO.read_value(C2) == 1):
                    self.current_keys.add(characters[1])
                if(GPIO.read_value(C3) == 1):
                    self.current_keys.add(characters[2])
                if(GPIO.read_value(C4) == 1):
                    self.current_keys.add(characters[3])
                GPIO.write_value(line, 0)

            def run():
                while not stop_event.is_set():
                    self.last_keys, self.current_keys = self.current_keys, set()

                    readLine(R1, ["1","2","3","A"])
                    readLine(R2, ["4","5","6","B"])
                    readLine(R3, ["7","8","9","C"])
                    readLine(R4, ["*","0","#","D"])

                    for c in self.current_keys.difference(self.last_keys):
                        self.state_changed(c)

                    time.sleep(0.2)

            t = threading.Thread(target=run)
            t.start()
            threads.append(t)
        else:
            possible_keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "*", "#"]

            def run():
                while not stop_event.is_set():
                    if random.random() < 0.5:
                        self.state_changed(random.sample(possible_keys, 1)[0])

                    time.sleep(1)

            t = threading.Thread(target=run)
            t.start()
            threads.append(t)