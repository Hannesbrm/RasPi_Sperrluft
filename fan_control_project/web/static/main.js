const socket = io();

const temp1El = document.getElementById('temp1');
const temp2El = document.getElementById('temp2');
const pwmEl = document.getElementById('pwm');
const modeEl = document.getElementById('mode');
const modeSelect = document.getElementById('modeSelect');
const modeForm = document.getElementById('modeForm');
const manualPwmForm = document.getElementById('manualPwmForm');
const tempChartCtx = document.getElementById('tempChart').getContext('2d');

const maxPoints = 50;
const labels = [];
const temp1Data = [];
const temp2Data = [];

const tempChart = new Chart(tempChartCtx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [
            {
                label: 'Temperature 1',
                borderColor: 'red',
                fill: false,
                data: temp1Data
            },
            {
                label: 'Temperature 2',
                borderColor: 'blue',
                fill: false,
                data: temp2Data
            }
        ]
    },
    options: {
        animation: false,
        responsive: true,
        scales: {
            x: {
                display: true
            },
            y: {
                display: true
            }
        }
    }
});

socket.on('state_update', data => {
    if (data.temperature1 !== undefined) {
        temp1El.textContent = Number(data.temperature1).toFixed(1);
    }
    if (data.temperature2 !== undefined) {
        temp2El.textContent = Number(data.temperature2).toFixed(1);
    }
    if (data.pwm1 !== undefined) {
        pwmEl.textContent = Number(data.pwm1).toFixed(1);
    }
    if (data.mode !== undefined) {
        modeEl.textContent = data.mode;
        modeSelect.value = data.mode;
    }

    if (data.temperature1 !== undefined && data.temperature2 !== undefined) {
        labels.push(new Date().toLocaleTimeString());
        temp1Data.push(parseFloat(data.temperature1));
        temp2Data.push(parseFloat(data.temperature2));
        if (labels.length > maxPoints) {
            labels.shift();
            temp1Data.shift();
            temp2Data.shift();
        }
        tempChart.update();
    }
});

// send setpoint
const setpointForm = document.getElementById('setpointForm');
setpointForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(document.getElementById('setpointInput').value);
    if (!isNaN(value)) {
        socket.emit('set_setpoint', { value });
        document.getElementById('setpointInput').value = '';
    }
});

// send alarm threshold
const alarmForm = document.getElementById('alarmForm');
alarmForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(document.getElementById('alarmInput').value);
    if (!isNaN(value)) {
        socket.emit('set_alarm_threshold', { value });
        document.getElementById('alarmInput').value = '';
    }
});

// send manual pwm
manualPwmForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(document.getElementById('manualPwmInput').value);
    if (!isNaN(value)) {
        socket.emit('set_manual_pwm', { value });
        document.getElementById('manualPwmInput').value = '';
    }
});

// change mode
modeForm.addEventListener('submit', e => {
    e.preventDefault();
    socket.emit('set_mode', { mode: modeSelect.value });
});
