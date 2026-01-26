import json
import influxDB
import paho.mqtt.client as mqtt
import time
import logging

MQTT_TOPIC = 'iot/sensors'
MQTT_BROKER = 'mosquitto'
MQTT_PORT = 1883

def on_connect(client, userdata, flags, rc):
    print("MQTT connected")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        print("Message received")
        data = json.loads(msg.payload.decode())
        print(f"{data}")
        influxDB.write_sensor_data(data)
    except Exception as e:
        print("MQTT error:", e)

def start_mqtt():
    
    client = mqtt.Client(client_id="flask_subscriber", clean_session=True)
    client.on_connect = on_connect
    client.on_message = on_message
    client.enable_logger()
    logging.basicConfig(level=logging.DEBUG)

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception as e:
            print(f"Connect failed: {e}, retrying...")
            time.sleep(2)

    client.loop_start()