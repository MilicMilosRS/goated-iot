import json
import influxDB
import paho.mqtt.client as mqtt

MQTT_TOPIC = 'iot/sensors'
MQTT_BROKER = 'localhost'
MQTT_PORT = '1883'

def on_connect(client, userdata, flags, rc):
    print("MQTT connected")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        write_to_influx(data)
    except Exception as e:
        print("MQTT error:", e)

def write_to_influx(data):
    if isinstance(data, dict):
        data = [data]
    influxDB.write_sensor_data(data)

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()