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

def write_sensor_data(pi_id, device, entry):
    point = (
        Point(entry["sensor"])
        .tag("pi", pi_id)
        .tag("device", device)
        .tag("simulated", str(entry["simulated"]))
        .field("value", entry["value"])
        .time(entry["timestamp"])
    )
    write_api.write(bucket=BUCKET, record=point)
