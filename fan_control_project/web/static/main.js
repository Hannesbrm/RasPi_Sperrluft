const socket = io();

const temp1El = document.getElementById('temp1');
const temp2El = document.getElementById('temp2');
const pwmEl = document.getElementById('pwm');
const modeEl = document.getElementById('mode');
const modeToggle = document.getElementById('modeToggle');
const manualPwmForm = document.getElementById('manualPwmForm');
const manualPwmInput = document.getElementById('manualPwmInput');
const setpointEl = document.getElementById('setpoint');
const alarmThresholdEl = document.getElementById('alarmThreshold');
const alarmIndicatorEl = document.getElementById('alarmIndicator');
const setpointInput = document.getElementById('setpointInput');
const alarmInput = document.getElementById('alarmInput');
const pidForm = document.getElementById('pidForm');
const kpInput = document.getElementById('kpInput');
const kiInput = document.getElementById('kiInput');
const kdInput = document.getElementById('kdInput');
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
        const manual = data.mode === 'manual';
        modeToggle.checked = manual;
        manualPwmForm.style.display = manual ? 'block' : 'none';
    }
    if (data.setpoint !== undefined) {
        const formatted = Number(data.setpoint).toFixed(1);
        setpointEl.textContent = formatted;
        setpointInput.placeholder = formatted;
    }
    if (data.alarm_threshold !== undefined) {
        const formatted = Number(data.alarm_threshold).toFixed(1);
        alarmThresholdEl.textContent = formatted;
        alarmInput.placeholder = formatted;
    }
    if (
        data.temperature2 !== undefined &&
        data.alarm_threshold !== undefined
    ) {
        const t2 = parseFloat(data.temperature2);
        const threshold = parseFloat(data.alarm_threshold);
        const alarmAktiv = t2 > threshold;
        if (alarmIndicatorEl) {
            if (alarmAktiv) {
                alarmIndicatorEl.className = 'alarm-box danger';
                alarmIndicatorEl.innerHTML = '<span class="icon">🔴</span> ALARM AKTIV';
            } else {
                alarmIndicatorEl.className = 'alarm-box safe';
                alarmIndicatorEl.innerHTML = '<span class="icon">🟢</span> Kein Alarm';
            }
        }
    }
    if (data.kp !== undefined) {
        kpInput.placeholder = Number(data.kp).toFixed(2);
    }
    if (data.ki !== undefined) {
        kiInput.placeholder = Number(data.ki).toFixed(2);
    }
    if (data.kd !== undefined) {
        kdInput.placeholder = Number(data.kd).toFixed(2);
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
    const value = parseFloat(setpointInput.value);
    if (!isNaN(value)) {
        socket.emit('set_setpoint', { value });
        setpointInput.value = '';
    }
});

// send alarm threshold
const alarmForm = document.getElementById('alarmForm');
alarmForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(alarmInput.value);
    if (!isNaN(value)) {
        socket.emit('set_alarm_threshold', { value });
        alarmInput.value = '';
    }
});

// send manual pwm
manualPwmForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(manualPwmInput.value);
    if (!isNaN(value)) {
        socket.emit('set_manual_pwm', { value });
        manualPwmInput.value = '';
    }
});

// send PID parameters
pidForm.addEventListener('submit', e => {
    e.preventDefault();
    const kp = parseFloat(kpInput.value);
    const ki = parseFloat(kiInput.value);
    const kd = parseFloat(kdInput.value);
    const payload = {};
    if (!isNaN(kp)) payload.kp = kp;
    if (!isNaN(ki)) payload.ki = ki;
    if (!isNaN(kd)) payload.kd = kd;
    if (Object.keys(payload).length > 0) {
        socket.emit('set_pid_params', payload);
        kpInput.value = '';
        kiInput.value = '';
        kdInput.value = '';
    }
});

// change mode
modeToggle.addEventListener('change', () => {
    const mode = modeToggle.checked ? 'manual' : 'auto';
    socket.emit('set_mode', { mode });
    manualPwmForm.style.display = modeToggle.checked ? 'block' : 'none';
});
