import threading
import queue
import time
import json
import paho.mqtt.client as mqtt
from influx_writer import write_api, bucket
from influxdb_client import Point
from influxdb_client.client.write_api import WritePrecision

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
        last_flush = time.time()

        while not self.stop_event.is_set():
            try:
                data = data_queue.get(timeout=0.5)
                batch.append(data)

                if (
                    len(batch) >= self.batch_size or
                    time.time() - last_flush >= self.interval
                ):
                    self.flush(batch)
                    batch.clear()
                    last_flush = time.time()

            except queue.Empty:
                continue

        if batch:
            self.flush(batch)

    def flush(self, batch):
        for data in batch:
            measurement = data["sensor"]

            tags = {
                "device": data["sensor_device"],
                "pi": data["pi"],
                "simulated": str(data["simulated"])
            }

            fields = {}

            if "fields" in data:
                for key in data["fields"]:
                    value = data.get(key)
                    if isinstance(value, (int, float)):
                        fields[key] = value
            elif "value" in data:
                v = data["value"]
                if measurement in ["Button", "Motion sensor"]:
                    fields["state"] = 1 if v in ["Pressed", "Motion detected"] else 0

                else:
                    try:
                        fields["value"] = float(v)
                    except (ValueError, TypeError):
                        continue 

            if not fields:
                continue

            point = Point(measurement)

            for k, v in tags.items():
                point = point.tag(k, v)

            for k, v in fields.items():
                point = point.field(k, v)

            point = point.time(data["timestamp"], WritePrecision.NS)

            write_api.write(bucket="iot", record=point)
