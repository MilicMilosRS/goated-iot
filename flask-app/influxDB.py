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
                .tag("device", str(item['sensor_device']))
                .time(item["timestamp"])
            )

            if "value" in item:
                point.field("value", item["value"])

            if 'fields' in item:
                for f in item['fields']:
                    point.field(f, item[f])

            write_api.write(bucket=BUCKET, record=point)
        except Exception as e:
            print("Influx write error:", e)
