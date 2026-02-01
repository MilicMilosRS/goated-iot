import random
import threading
import time
from mqtt_daemon import data_queue

class Gyro():
    def __init__(self, cfg):
        self.cfg = cfg
    
    def state_changed(self, accel, gyro):
        data = {
            'sensor': 'Gyroscope',
            'sensor_device': self.cfg['sensor'],
            'pi': self.cfg['pi'],
            'simulated': self.cfg['simulated'],
            "accel_x": accel[0],
            "accel_y": accel[1],
            "accel_z": accel[2],
            "gyro_x": gyro[0],
            "gyro_y": gyro[1],
            "gyro_z": gyro[2],
            "fields": ["accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"],
            'timestamp': time.time_ns()
        }
        data_queue.put(data)

    def start(self, threads: list, stop_event: threading.Event):
        if not self.cfg['simulated']:
            from components.MPU6050.MPU6050 import MPU6050
            mpu = MPU6050()
            mpu.dmp_initialize()
            def loop():
                while not stop_event.is_set():
                    accel = mpu.get_acceleration()      #get accelerometer data
                    gyro = mpu.get_rotation()           #get gyroscope data
                    self.state_changed(accel, gyro)
                    time.sleep(self.cfg['delay'])

            t = threading.Thread(target=loop)
            t.start()
            threads.append(t)
        else:
            def loop():
                while not stop_event.is_set():
                    accel = [random.random(), random.random(), random.random()]
                    gyro = [random.random(), random.random(), random.random()]
                    self.state_changed(accel, gyro)
                    time.sleep(self.cfg['delay'])
            t = threading.Thread(target=loop)
            t.start()
            threads.append(t)