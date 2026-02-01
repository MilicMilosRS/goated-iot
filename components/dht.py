
import random
from threading import Event, Thread
import time
from components.local_gpio import LocalGPIO
from mqtt_daemon import data_queue

class DHT(object):
	DHTLIB_OK = 0
	DHTLIB_ERROR_CHECKSUM = -1
	DHTLIB_ERROR_TIMEOUT = -2
	DHTLIB_INVALID_VALUE = -999
	
	DHTLIB_DHT11_WAKEUP = 0.020#0.018		#18ms
	DHTLIB_TIMEOUT = 0.0001			#100us
	
	humidity = 0
	temperature = 0

	def state_changed(self, code):
		data = {
            'sensor': 'DHT',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
			"temperature": self.temperature,
			"humidity": self.humidity,
			"code": code,
			"fields": ["temperature", "humidity", "code"],
            'timestamp': time.time_ns()
        }
		data_queue.put(data)
	
	def __init__(self,cfg):
		self.cfg = cfg
		self.pin = cfg['pin']
		self.bits = [0,0,0,0,0]
		self.GPIO = LocalGPIO()

	#Read DHT sensor, store the original data in bits[]	
	def readSensor(self,pin,wakeupDelay):
		mask = 0x80
		idx = 0
		self.bits = [0,0,0,0,0]
		self.GPIO.setup_out(pin)
		self.GPIO.write_value(pin, False)
		time.sleep(wakeupDelay)
		self.GPIO.write_value(pin, True)
		#time.sleep(40*0.000001)
		self.GPIO.setup_in(pin)


		loopCnt = self.DHTLIB_TIMEOUT
		t = time.time()
		while(self.GPIO.read_value(pin) == False):
			if((time.time() - t) > loopCnt):
				#print ("Echo LOW")
				return self.DHTLIB_ERROR_TIMEOUT
		t = time.time()
		while(self.GPIO.read_value(pin) == True):
			if((time.time() - t) > loopCnt):
				#print ("Echo HIGH")
				return self.DHTLIB_ERROR_TIMEOUT
		for i in range(0,40,1):
			t = time.time()
			while(self.GPIO.read_value(pin) == False):
				if((time.time() - t) > loopCnt):
					#print ("Data Low %d"%(i))
					return self.DHTLIB_ERROR_TIMEOUT
			t = time.time()
			while(self.GPIO.read_value(pin) == True):
				if((time.time() - t) > loopCnt):
					#print ("Data HIGH %d"%(i))
					return self.DHTLIB_ERROR_TIMEOUT		
			if((time.time() - t) > 0.00005):	
				self.bits[idx] |= mask
			#print("t : %f"%(time.time()-t))
			mask >>= 1
			if(mask == 0):
				mask = 0x80
				idx += 1	
		#print (self.bits)
		self.GPIO.setup_out(pin)
		self.GPIO.write_value(pin, True)
		return self.DHTLIB_OK
	#Read DHT sensor, analyze the data of temperature and humidity
	def readDHT11(self):
		rv = self.readSensor(self.pin,self.DHTLIB_DHT11_WAKEUP)
		if (rv is not self.DHTLIB_OK):
			self.humidity = self.DHTLIB_INVALID_VALUE
			self.temperature = self.DHTLIB_INVALID_VALUE
			return rv
		self.humidity = self.bits[0]
		self.temperature = self.bits[2] + self.bits[3]*0.1
		sumChk = ((self.bits[0] + self.bits[1] + self.bits[2] + self.bits[3]) & 0xFF)
		if(self.bits[4] is not sumChk):
			return self.DHTLIB_ERROR_CHECKSUM
		return self.DHTLIB_OK
	
	def start(self, threads: list, stop_event: Event):
		if not self.cfg['simulated']:
			def run():
				while not stop_event.is_set():
					check = self.readDHT11()
					code = parseCheckCode(check)
					self.state_changed(code)
					time.sleep(self.cfg['delay'])
			
			t = Thread(target=run)
			t.start()
			threads.append(t)
		else:
			def run():
				while not stop_event.is_set():
					self.temperature = random.random() * 30
					self.humidity = random.random() * 80
					self.state_changed("DHTLIB_OK")
					time.sleep(self.cfg['delay'])
			
			t = Thread(target=run)
			t.start()
			threads.append(t)

def parseCheckCode(code):
	if code == 0:
		return "DHTLIB_OK"
	elif code == -1:
		return "DHTLIB_ERROR_CHECKSUM"
	elif code == -2:
		return "DHTLIB_ERROR_TIMEOUT"
	elif code == -999:
		return "DHTLIB_INVALID_VALUE"


def run_dht_loop(dht, delay, callback, stop_event):
		while True:
			check = dht.readDHT11()
			code = parseCheckCode(check)
			humidity, temperature = dht.humidity, dht.temperature
			callback(humidity, temperature, code)
			if stop_event.is_set():
					break
			time.sleep(delay)  # Delay between readings
