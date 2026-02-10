from influxdb_client import InfluxDBClient, WritePrecision

client = InfluxDBClient(
    url="http://localhost:8086",
    token="gas",
    org="iot"
)

write_api = client.write_api(write_precision=WritePrecision.NS)
bucket = "iot"
