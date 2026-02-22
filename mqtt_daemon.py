import threading
import queue
import time
import json
import paho.mqtt.client as mqtt

data_queue = queue.Queue(maxsize=10_000)

class MqttDaemon(threading.Thread):
    def __init__(self, broker, stop_event, topic='iot/sensors',
                 subscribe_topic=None, on_message_callback=None,
                 batch_size=10, interval=2):
        super().__init__(daemon=True)
        self.topic = topic
        self.subscribe_topic = subscribe_topic
        self.on_message_callback = on_message_callback
        self.batch_size = batch_size
        self.interval = interval
        self.stop_event = stop_event

        self.client = mqtt.Client()

        if self.subscribe_topic and self.on_message_callback:
            self.client.on_message = self._on_message
            self.client.on_connect = self._on_connect

        self.client.connect(broker, 1883, 60)

    def _on_connect(self, client, userdata, flags, rc):
        client.subscribe(self.subscribe_topic)

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            self.on_message_callback(data)
        except Exception as e:
            print("MqttDaemon message error:", e)

    def run(self):
        self.client.loop_start()
        batch = []
        timer = time.time()
        while not self.stop_event.is_set():
            try:
                item = data_queue.get(timeout=self.interval)
                batch.append(item)

                if len(batch) >= self.batch_size or(time.time() - timer > 4 and len(batch) > 0):
                    timer = time.time()
                    self.flush(batch)
                    batch.clear()

            except queue.Empty:
                if batch:
                    self.flush(batch)
                    batch.clear()

        if batch:
            self.flush(batch)

        self.client.loop_stop()

    def flush(self, batch):
        print("FLUSHED")
        payload = json.dumps(batch)
        self.client.publish(self.topic, payload)
