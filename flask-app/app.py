import json
import time
import threading
from flask import Flask, jsonify, request, Response, render_template
from mqtt_client import (
    start_mqtt,
    alarm_system, sse_register, sse_unregister,
    kitchen_timer, brgb,
)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


# SSE

@app.route("/events")
def events():
    q = sse_register()

    def stream():
        state = {
            "event":          "STATE_SYNC",
            "alarm_active":   alarm_system.alarm_active,
            "security_armed": alarm_system.security_armed,
            "person_count":   alarm_system.person_count,
            "timer":          kitchen_timer.status,
            "brgb":           brgb.status,
            "timestamp":      time.time_ns(),
        }
        yield f"data: {json.dumps(state)}\n\n"

        try:
            while True:
                try:
                    payload = q.get(timeout=20)
                    yield f"data: {json.dumps(payload)}\n\n"
                except Exception:
                    yield ": heartbeat\n\n"
        finally:
            sse_unregister(q)

    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# Alarm
@app.route("/status")
def status():
    return jsonify({
        "alarm_active":   alarm_system.alarm_active,
        "security_armed": alarm_system.security_armed,
        "person_count":   alarm_system.person_count,
        "timer":          kitchen_timer.status,
        "brgb":           brgb.status,
    })


@app.route("/pin", methods=["POST"])
def enter_pin():
    body = request.get_json(force=True, silent=True) or {}
    pin  = str(body.get("pin", ""))
    if not pin:
        return jsonify({"error": "pin is required"}), 400
    alarm_system.handle_pin(pin=pin, source="WEB")
    return jsonify({
        "alarm_active":   alarm_system.alarm_active,
        "security_armed": alarm_system.security_armed,
    })


# Timer
@app.route("/timer", methods=["GET"])
def timer_status():
    return jsonify(kitchen_timer.status)


@app.route("/timer/set", methods=["POST"])
def timer_set():
    """Body: { "seconds": 300 }"""
    body = request.get_json(force=True, silent=True) or {}
    try:
        seconds = int(body["seconds"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "seconds (int) is required"}), 400
    if seconds < 0:
        return jsonify({"error": "seconds must be >= 0"}), 400
    kitchen_timer.set_timer(seconds)
    return jsonify(kitchen_timer.status)


@app.route("/timer/add", methods=["POST"])
def timer_add():
    """Body: { "seconds": 30 }"""
    body = request.get_json(force=True, silent=True) or {}
    try:
        seconds = int(body["seconds"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "seconds (int) is required"}), 400
    kitchen_timer.add_seconds(seconds)
    return jsonify(kitchen_timer.status)


@app.route("/timer/config", methods=["POST"])
def timer_config():
    """Body: { "btn_add_seconds": 30 } – configures how many seconds BTN adds."""
    body = request.get_json(force=True, silent=True) or {}
    try:
        n = int(body["btn_add_seconds"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "btn_add_seconds (int) is required"}), 400
    kitchen_timer.btn_add_seconds = max(1, n)
    return jsonify({"btn_add_seconds": kitchen_timer.btn_add_seconds})


@app.route("/timer/cancel", methods=["POST"])
def timer_cancel():
    kitchen_timer.cancel()
    return jsonify(kitchen_timer.status)


#BRGB

@app.route("/brgb", methods=["GET"])
def brgb_status():
    return jsonify(brgb.status)

@app.route("/brgb/color", methods=["POST"])
def brgb_color():
    body = request.get_json(force=True, silent=True) or {}
    r = bool(body.get("r", brgb.r))
    g = bool(body.get("g", brgb.g))
    b = bool(body.get("b", brgb.b))
    brgb.set_color(r, g, b)
    return jsonify(brgb.status)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    app.run(host="0.0.0.0", port=5000, threaded=True)