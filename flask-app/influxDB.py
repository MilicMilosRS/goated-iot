from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUX_URL = "http://localhost:8086"
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
    point = (
        Point(data["sensor"])
        .tag("pi", data["pi"])
        .tag("simulated", data["simulated"])
        .field("value", data["value"])
        .time(data["timestamp"])
    )
    write_api.write(bucket=BUCKET, record=point)
