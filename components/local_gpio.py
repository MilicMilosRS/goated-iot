class LocalGPIO:
    def __init__(self):
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.GPIO.setmode(GPIO.BCM)
        except Exception:
            self.GPIO = None

    def setup_in_pull_up(self, pin):
        if self.GPIO is None:
            return
        else:
            self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)

    def setup_in_pull_down(self, pin):
        if self.GPIO is None:
            return
        else:
            self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_DOWN)

    def setup_in(self, pin):
        if self.GPIO is None:
            return
        else:
            self.GPIO.setup(pin, self.GPIO.IN)

    def setup_out(self, pin):
        if self.GPIO is None:
            return
        else:
            self.GPIO.setup(pin, self.GPIO.OUT)

    def read_value(self, pin):
        if self.GPIO is None:
            return False
        return self.GPIO.input(pin)
    
    def write_value(self, pin, val: bool):
        if self.GPIO is None:
            return 0
        return self.GPIO.output(pin, 1 if val else 0)
    
    def add_event_detect(self, pin, edge, callback=None, bouncetime=None):
        if edge == "RISING":
            self.GPIO.add_event_detect(pin, self.GPIO.RISING, callback=callback, bouncetime=bouncetime)
        elif edge == "FALLING":
            self.GPIO.add_event_detect(pin, self.GPIO.FALLING, callback=callback, bouncetime=bouncetime)
        else:
            self.GPIO.add_event_detect(pin, self.GPIO.BOTH, callback=callback, bouncetime=bouncetime)
        
    