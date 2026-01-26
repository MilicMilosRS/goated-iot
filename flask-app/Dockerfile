FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install flask paho-mqtt influxdb-client

CMD ["python", "app.py"]