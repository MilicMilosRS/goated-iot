// MQTT Setup
const client = mqtt.connect("ws://localhost:9001"); // MQTT over WebSocket port

let peopleCount = 0;
let alarmActive = false;

const sensorList = document.getElementById("sensor-list");
const alarmDiv = document.getElementById("alarm-status");
const peopleNum = document.getElementById("people-num");
const pinInput = document.getElementById("pin-input");
const pinSubmit = document.getElementById("pin-submit");
const timerDiv = document.getElementById("timer");

let stopwatchSeconds = 0;
let stopwatchInterval = null;

// Helper to add sensor to list
function updateSensor(sensor, value) {
    let li = document.getElementById(sensor);
    if (!li) {
        li = document.createElement("li");
        li.id = sensor;
        sensorList.appendChild(li);
    }
    li.textContent = `${sensor}: ${value}`;
}

// Handle ALARM logic
function triggerAlarm(reason) {
    alarmActive = true;
    alarmDiv.textContent = "ALARM ACTIVE! (" + reason + ")";
    alarmDiv.classList.add("active");
    console.log("ALARM TRIGGERED:", reason);
}

function resetAlarm() {
    alarmActive = false;
    alarmDiv.textContent = "Inactive";
    alarmDiv.classList.remove("active");
}


// Handle MQTT messages
client.on("connect", () => {
    client.subscribe("iot/sensors");
});

client.on("message", (topic, message) => {
    const data = JSON.parse(message.toString());
    updateSensor(data.sensor + "-" + data.sensor_device, data.value);

    // People counting logic (example for DPIR + DUS)
    if (data.sensor.startsWith("Motion") && data.sensor_device.startsWith("DPIR")) {
        // Use DUS distance from last few seconds to decide entering/exiting
        peopleCount += data.value === "Motion detected" ? 1 : 0; 
        peopleNum.textContent = peopleCount;
    }

    // Door sensor triggering alarm
    if (data.sensor.startsWith("Button") && data.value === "Pressed") {
        triggerAlarm("Door held open");
    }

    // GSG movement triggers alarm
    if (data.sensor === "Gyroscope") {
        const move = Math.abs(data.accel_x) + Math.abs(data.accel_y) + Math.abs(data.accel_z);
        if (move > 2) triggerAlarm("Slavska icon moved");
    }

    // Motion triggers alarm if nobody inside
    if (peopleCount === 0 && data.sensor.startsWith("Motion") && data.value === "Motion detected") {
        triggerAlarm("Motion detected with empty building");
    }
});

// PIN logic
pinSubmit.onclick = () => {
    if (pinInput.value === "1234") { // example PIN
        setTimeout(() => {
            resetAlarm();
        }, 10000); // deactivate after 10 seconds
    }
};

// Stopwatch logic
document.getElementById("add-time").onclick = () => {
    stopwatchSeconds += 10; // default add 10 sec
    if (!stopwatchInterval) startStopwatch();
};

function startStopwatch() {
    stopwatchInterval = setInterval(() => {
        let minutes = Math.floor(stopwatchSeconds / 60).toString().padStart(2,'0');
        let seconds = (stopwatchSeconds % 60).toString().padStart(2,'0');
        timerDiv.textContent = `${minutes}:${seconds}`;
        if (stopwatchSeconds > 0) stopwatchSeconds--;
        else clearInterval(stopwatchInterval);
    }, 1000);
}

// Light control
document.getElementById("light-on").onclick = () => console.log("Light ON");
document.getElementById("light-off").onclick = () => console.log("Light OFF");
document.getElementById("light-color").oninput = (e) => console.log("Color:", e.target.value);

// Camera (browser camera example)
navigator.mediaDevices.getUserMedia({ video: true })
.then(stream => {
    document.getElementById("cam-feed").srcObject = stream;
})
.catch(err => console.log("Camera error:", err));
