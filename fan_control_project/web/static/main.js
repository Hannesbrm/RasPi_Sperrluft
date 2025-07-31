const socket = io();

const temp1El = document.getElementById('temp1');
const temp2El = document.getElementById('temp2');
const temp1StatusEl = document.getElementById('temp1Status');
const temp2StatusEl = document.getElementById('temp2Status');
const pwmEl = document.getElementById('pwm');
const modeEl = document.getElementById('mode');
const modeToggle = document.getElementById('modeToggle');
const manualPwmForm = document.getElementById('manualPwmForm');
const manualPwmInput = document.getElementById('manualPwmInput');
const alarmPwmForm = document.getElementById('alarmPwmForm');
const alarmPwmInput = document.getElementById('alarmPwmInput');
const minPwmForm = document.getElementById('minPwmForm');
const minPwmInput = document.getElementById('minPwmInput');
const postrunForm = document.getElementById('postrunForm');
const postrunInput = document.getElementById('postrunInput');
const setpointEl = document.getElementById('setpoint');
const alarmThresholdEl = document.getElementById('alarmThreshold');
const alarmIndicatorEl = document.getElementById('alarmIndicator');
const mainHeader = document.getElementById('main-header');
const rebootButton = document.getElementById('rebootButton');
const setpointInput = document.getElementById('setpointInput');
const alarmInput = document.getElementById('alarmInput');
const pidForm = document.getElementById('pidForm');
const kpInput = document.getElementById('kpInput');
const kiInput = document.getElementById('kiInput');
const kdInput = document.getElementById('kdInput');
const tempChartCtx = document.getElementById('tempChart').getContext('2d');
const logContainer = document.getElementById('logContainer');

const maxPoints = 200;
const labels = [];
const temp1Data = [];
const temp2Data = [];
const pwmData = [];

const MIN_TEMP_RANGE = 5;
const minTempRangePlugin = {
    id: 'minTempRangePlugin',
    afterDataLimits: scale => {
        if (scale.id !== 'y') return;
        const range = scale.max - scale.min;
        if (range < MIN_TEMP_RANGE) {
            const mid = (scale.max + scale.min) / 2;
            // use suggestedMin/Max so automatic scaling still works
            scale.options.suggestedMin = mid - MIN_TEMP_RANGE / 2;
            scale.options.suggestedMax = mid + MIN_TEMP_RANGE / 2;
        } else {
            // clear suggestions when not needed
            scale.options.suggestedMin = undefined;
            scale.options.suggestedMax = undefined;
        }
    }
};

const tempChart = new Chart(tempChartCtx, {
    type: 'line',
    plugins: [minTempRangePlugin],
    data: {
        labels: labels,
        datasets: [
            {
                label: 'Temperature 1',
                borderColor: 'red',
                fill: false,
                data: temp1Data,
                pointRadius: 0
            },
            {
                label: 'Temperature 2',
                borderColor: 'blue',
                fill: false,
                data: temp2Data,
                pointRadius: 0
            },
            {
                label: 'PWM',
                borderColor: 'green',
                fill: false,
                data: pwmData,
                yAxisID: 'y1',
                pointRadius: 0
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
                position: 'left',
                title: {
                    display: true,
                    text: 'Temperatur (°C)'
                }
            },
            y1: {
                position: 'right',
                title: {
                    display: true,
                    text: 'PWM (%)'
                },
                grid: {
                    drawOnChartArea: false
                },
                suggestedMin: 0,
                suggestedMax: 100
            }
        }
    }
});

function showFeedback(id) {
    const el = document.getElementById(id);
    if (el) {
        el.style.display = 'block';
        setTimeout(() => {
            el.style.display = 'none';
        }, 2000);
    }
}

socket.on('state_update', data => {
    if (data.temperature1 !== undefined) {
        if (data.temperature1 === null) {
            temp1El.textContent = '--';
        } else {
            temp1El.textContent = Number(data.temperature1).toFixed(1);
        }
    }
    if (data.temperature2 !== undefined) {
        if (data.temperature2 === null) {
            temp2El.textContent = '--';
        } else {
            temp2El.textContent = Number(data.temperature2).toFixed(1);
        }
    }
    if (data.status1 !== undefined && temp1StatusEl) {
        temp1StatusEl.textContent = data.status1 === 'ok' ? '' : `Sensorfehler: ${data.status1}`;
    }
    if (data.status2 !== undefined && temp2StatusEl) {
        temp2StatusEl.textContent = data.status2 === 'ok' ? '' : `Sensorfehler: ${data.status2}`;
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
    if (data.alarm_pwm !== undefined) {
        alarmPwmInput.placeholder = Number(data.alarm_pwm).toFixed(0);
    }
    if (data.min_pwm !== undefined) {
        minPwmInput.placeholder = Number(data.min_pwm).toFixed(0);
    }
    if (data.postrun_seconds !== undefined) {
        postrunInput.placeholder = Number(data.postrun_seconds).toFixed(0);
    }
    if (data.manual_pwm !== undefined) {
        manualPwmInput.placeholder = Number(data.manual_pwm).toFixed(0);
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
        if (mainHeader) {
            mainHeader.style.backgroundColor = alarmAktiv ? '#cc0000' : '#0077cc';
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

    if (
        data.temperature1 !== undefined &&
        data.temperature2 !== undefined &&
        data.pwm1 !== undefined
    ) {
        labels.push(new Date().toLocaleTimeString());
        temp1Data.push(data.temperature1 === null ? null : parseFloat(data.temperature1));
        temp2Data.push(data.temperature2 === null ? null : parseFloat(data.temperature2));
        pwmData.push(parseFloat(data.pwm1));
        if (labels.length > maxPoints) {
            labels.shift();
            temp1Data.shift();
            temp2Data.shift();
            pwmData.shift();
        }
        tempChart.update();
    }
});

setpointForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(setpointInput.value);
    if (!isNaN(value)) {
        socket.emit('set_setpoint', { value });
        setpointInput.value = '';
        showFeedback('setpointFeedback');
    }
});

alarmForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(alarmInput.value);
    if (!isNaN(value)) {
        socket.emit('set_alarm_threshold', { value });
        alarmInput.value = '';
        showFeedback('alarmFeedback');
    }
});

manualPwmForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(manualPwmInput.value);
    if (!isNaN(value)) {
        socket.emit('set_manual_pwm', { value });
        manualPwmInput.value = '';
        showFeedback('manualFeedback');
    }
});

alarmPwmForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(alarmPwmInput.value);
    if (!isNaN(value)) {
        socket.emit('set_alarm_pwm', { value });
        alarmPwmInput.value = '';
        showFeedback('alarmPwmFeedback');
    }
});

minPwmForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(minPwmInput.value);
    if (!isNaN(value)) {
        socket.emit('set_min_pwm', { value });
        minPwmInput.value = '';
        showFeedback('minPwmFeedback');
    }
});

postrunForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(postrunInput.value);
    if (!isNaN(value)) {
        socket.emit('set_postrun_seconds', { value });
        postrunInput.value = '';
        showFeedback('postrunFeedback');
    }
});

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
        showFeedback('pidFeedback');
    }
});

modeToggle.addEventListener('change', () => {
    const mode = modeToggle.checked ? 'manual' : 'auto';
    socket.emit('set_mode', { mode });
    manualPwmForm.style.display = modeToggle.checked ? 'block' : 'none';
});

// Listen for system state updates to adjust header color
socket.on('system_state', data => {
    if (!mainHeader) return;
    if (data.alarm_active === true) {
        mainHeader.style.backgroundColor = '#cc0000';
    } else if (data.alarm_active === false) {
        mainHeader.style.backgroundColor = '#0077cc';
    }
});

socket.on('logs_update', logs => {
    if (!logContainer) return;
    logContainer.innerHTML = '';
    logs.forEach(entry => {
        const div = document.createElement('div');
        div.textContent = entry.message;
        div.classList.add('log-entry', `log-${entry.level}`);
        logContainer.appendChild(div);
    });
    logContainer.scrollTop = logContainer.scrollHeight;
});

if (rebootButton) {
    rebootButton.addEventListener('click', () => {
        if (confirm('Raspberry Pi neustarten?')) {
            socket.emit('request_reboot');
        }
    });
}

socket.on('reboot_ack', () => {
    alert('wird neu gestartet...');
});

