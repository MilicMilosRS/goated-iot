from flask import Flask
import threading
from mqtt_client import start_mqtt

app = Flask(__name__)

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    mqtt_thread = threading.Thread(target=start_mqtt)
    mqtt_thread.start()

    app.run(host="0.0.0.0", port=5000)