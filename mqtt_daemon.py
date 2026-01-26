import threading
import queue
import time
import json
import paho.mqtt.client as mqtt

data_queue = queue.Queue(maxsize=10_000)

class MqttDaemon(threading.Thread):
    def __init__(self, broker, stop_event, topic='iot/sensors', batch_size=10, interval=2):
        super().__init__(daemon=True)
        self.topic = topic
        self.batch_size = batch_size
        self.interval = interval
        self.stop_event = stop_event

        self.client = mqtt.Client()
        self.client.connect(broker, 1883, 60)

    def run(self):
        batch = []

        while not self.stop_event.is_set():
            try:
                item = data_queue.get(timeout=self.interval)
                batch.append(item)

                if len(batch) >= self.batch_size:
                    self.flush(batch)
                    batch.clear()

            except queue.Empty:
                if batch:
                    self.flush(batch)
                    batch.clear()

        if batch:
            self.flush(batch)

    def flush(self, batch):
        print("FLUSHED")
        payload = json.dumps(batch)
        self.client.publish(self.topic, payload)