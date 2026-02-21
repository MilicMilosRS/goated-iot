import datetime
import random
import threading
import time
from components.local_gpio import LocalGPIO
from mqtt_daemon import data_queue

Buttons = [0x300ff22dd, 0x300ffc23d, 0x300ff629d, 0x300ffa857, 0x300ff9867, 0x300ffb04f, 0x300ff6897, 0x300ff02fd, 0x300ff30cf, 0x300ff18e7, 0x300ff7a85, 0x300ff10ef, 0x300ff38c7, 0x300ff5aa5, 0x300ff42bd, 0x300ff4ab5, 0x300ff52ad]  # HEX code list
ButtonsNames = ["LEFT",   "RIGHT",      "UP",       "DOWN",       "2",          "3",          "1",        "OK",        "4",         "5",         "6",         "7",         "8",          "9",        "*",         "0",        "#"]  # String list in same order as HEX list

class IRReceiver():
    def __init__(self, cfg):
        self.cfg = cfg
        self.GPIO = LocalGPIO()
        self.pin = cfg['pin']
    
    def state_changed(self, button_id):
        data = {
            'sensor': 'IR Receiver',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            "button_name": ButtonsNames[button_id],
            "button_value": Buttons[button_id],
            "fields": ["button_name", "button_value"],
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def getBinary(self):
        # Internal vars
        num1s = 0  # Number of consecutive 1s read
        binary = 1  # The binary value
        command = []  # The list to store pulse times in
        previousValue = 0  # The last value
        value = self.GPIO.read_value(self.pin)  # The current value

        # Waits for the sensor to pull pin low
        while value:
            time.sleep(0.0001) # This sleep decreases CPU utilization immensely
            value = self.GPIO.read_value(self.pin)  # The current value
            
        # Records start time
        startTime = datetime.now()
        
        while True:
            # If change detected in value
            if previousValue != value:
                now = datetime.now()
                pulseTime = now - startTime #Calculate the time of pulse
                startTime = now #Reset start time
                command.append((previousValue, pulseTime.microseconds)) #Store recorded data
                
            # Updates consecutive 1s variable
            if value:
                num1s += 1
            else:
                num1s = 0
            
            # Breaks program when the amount of 1s surpasses 10000
            if num1s > 10000:
                break
                
            # Re-reads pin
            previousValue = value
            value = self.GPIO.read_value(self.pin)  # The current value
            
        # Converts times to binary
        for (typ, tme) in command:
            if typ == 1: #If looking at rest period
                if tme > 1000: #If pulse greater than 1000us
                    binary = binary *10 +1 #Must be 1
                else:
                    binary *= 10 #Must be 0
                
        if len(str(binary)) > 34: #Sometimes, there is some stray characters
            binary = int(str(binary)[:34])
            
        return binary
        
    # Convert value to hex
    def convertHex(binaryValue):
        tmpB2 = int(str(binaryValue),2) #Temporarely propper base 2
        return hex(tmpB2)

    def start(self, threads: list, stop_event: threading.Event):
        if not self.cfg['simulated']:
            self.GPIO.setup_in(self.pin)

            def loop():
                while not stop_event.is_set():
                    inData = self.convertHex(self.getBinary()) #Runs subs to get incoming hex value
                    for button in range(len(Buttons)):#Runs through every value in list
                        if hex(Buttons[button]) == inData: #Checks this against incoming
                            self.state_changed(button) #Prints corresponding english name for button

            t = threading.Thread(target=loop)
            t.start()
            threads.append(t)
        else:
            def loop():
                while not stop_event.is_set():
                    self.state_changed(random.randrange(len(Buttons)))
                    time.sleep(self.cfg['delay'])
            t = threading.Thread(target=loop)
            t.start()
            threads.append(t)