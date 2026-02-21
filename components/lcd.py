import random
import threading
import time
from mqtt_daemon import data_queue
from components.local_gpio import LocalGPIO

class LCD():
    def __init__(self, cfg):
        self.cfg = cfg
        if not cfg['simulated']:
            from components.lcd_comps.Adafruit_LCD1602 import Adafruit_CharLCD
            from components.lcd_comps.PCF8574 import PCF8574_GPIO
            PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
            PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.
            try:
                self.mcp = PCF8574_GPIO(PCF8574_address)
            except:
                try:
                    self.mcp = PCF8574_GPIO(PCF8574A_address)
                except:
                    print ('I2C Address Error !')
            self.lcd = Adafruit_CharLCD(pin_rs=cfg['pin_rs'], pin_e=cfg['pin_e'], pins_db=cfg['pins'], GPIO=self.mcp)


    def state_changed(self, msg):
        data = {
            'sensor': 'LCD',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            'value': msg,
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def set_state(self, text: str):
        if not self.cfg['simulated']:
            self.mcp.output(3,1)     # turn on LCD backlight
            self.lcd.begin(16,2)     # set number of LCD lines and columns
            self.lcd.setCursor(0,0)
            self.lcd.message(text)
        else:
            print(f"LCD: {text}")
        self.state_changed(text)