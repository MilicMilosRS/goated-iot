from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUX_URL = "http://influxdb:8086"
INFLUX_TOKEN = "gas"
ORG = "iot"
BUCKET = "iot"

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=ORG
)

write_api = client.write_api(write_options=SYNCHRONOUS)

def write_sensor_data(data):
    if isinstance(data, dict):
        data = [data]
    
    for item in data:
        try:
            point = (
                Point(item["sensor"])
                .tag("pi", item["pi"])
                .tag("simulated", str(item["simulated"]))
                .field("value", item["value"])
                .time(item["timestamp"])
            )
            write_api.write(bucket=BUCKET, record=point)
        except Exception as e:
            print("Influx write error:", e)
