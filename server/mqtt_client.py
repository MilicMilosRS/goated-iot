import json
import paho.mqtt.client as mqtt
from influx import write_sensor_data

MQTT_BROKER = "localhost"
MQTT_TOPIC = "iot/sensors"

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())

    pi_id = payload["pi_id"]
    device = payload["device"]

    for entry in payload["data"]:
        write_sensor_data(pi_id, device, entry)

client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, 1883)
client.subscribe(MQTT_TOPIC)
client.loop_start()
