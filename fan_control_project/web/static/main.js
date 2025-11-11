const socket = io();

const temp1El = document.getElementById('temp1');
const temp2El = document.getElementById('temp2');
const temp1StatusEl = document.getElementById('temp1Status');
const temp2StatusEl = document.getElementById('temp2Status');
const temp1PinEl = document.getElementById('temp1Pin');
const temp2PinEl = document.getElementById('temp2Pin');
const outputEl = document.getElementById('output');
const modeEl = document.getElementById('mode');
const modeToggle = document.getElementById('modeToggle');
const swapToggle = document.getElementById('swapToggle');
const manualOutputForm = document.getElementById('manualOutputForm');
const manualOutputInput = document.getElementById('manualOutputInput');
const alarmOutputForm = document.getElementById('alarmOutputForm');
const alarmOutputInput = document.getElementById('alarmOutputInput');
const minOutputForm = document.getElementById('minOutputForm');
const minOutputInput = document.getElementById('minOutputInput');
const postrunForm = document.getElementById('postrunForm');
const postrunInput = document.getElementById('postrunInput');
const setpointEl = document.getElementById('setpoint');
const alarmThresholdEl = document.getElementById('alarmThreshold');
const temp1PinSettingEl = document.getElementById('temp1PinSetting');
const temp2PinSettingEl = document.getElementById('temp2PinSetting');
const alarmIndicatorEl = document.getElementById('alarmIndicator');
const postrunCountdownEl = document.getElementById('postrunCountdown');
const postrunSecondsEl = document.getElementById('postrunSeconds');
const mainHeader = document.getElementById('main-header');
const rebootButton = document.getElementById('rebootButton');
const darkModeToggle = document.getElementById('darkModeToggle');
const tcTypeSelect = document.getElementById('tcTypeSelect');
const setpointInput = document.getElementById('setpointInput');
const alarmInput = document.getElementById('alarmInput');
const pidForm = document.getElementById('pidForm');
const kpInput = document.getElementById('kpInput');
const kiInput = document.getElementById('kiInput');
const kdInput = document.getElementById('kdInput');
const tempChartCtx = document.getElementById('tempChart').getContext('2d');
const logContainer = document.getElementById('logContainer');
const logWrapper = document.getElementById('logWrapper');
const scanBtn = document.getElementById('scanBtn');
const testBtn = document.getElementById('testBtn');

let postrunRemaining = 0;
let postrunTimer = null;

const maxPoints = 200;
const labels = [];
const temp1Data = [];
const temp2Data = [];
const outputData = [];

const tempChart = new Chart(tempChartCtx, {
    type: 'line',
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
                label: 'Output',
                borderColor: 'green',
                fill: false,
                data: outputData,
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
                    text: 'Output (%)'
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

if (darkModeToggle) {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.classList.add('dark-mode');
        darkModeToggle.checked = true;
    }

    darkModeToggle.addEventListener('change', () => {
        if (darkModeToggle.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('theme', 'light');
        }
    });
}

socket.on('connect', () => {
    socket.emit('request_logs');
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

function updatePostrunCountdown(seconds) {
    postrunRemaining = seconds;
    if (postrunRemaining > 0) {
        if (postrunCountdownEl) {
            postrunCountdownEl.style.display = 'block';
            if (postrunSecondsEl) {
                postrunSecondsEl.textContent = postrunRemaining;
            }
        }
        if (!postrunTimer) {
            postrunTimer = setInterval(() => {
                if (postrunRemaining > 0) {
                    postrunRemaining -= 1;
                    if (postrunSecondsEl) {
                        postrunSecondsEl.textContent = postrunRemaining;
                    }
                } else {
                    if (postrunCountdownEl) {
                        postrunCountdownEl.style.display = 'none';
                    }
                    clearInterval(postrunTimer);
                    postrunTimer = null;
                }
            }, 1000);
        }
    } else {
        if (postrunCountdownEl) {
            postrunCountdownEl.style.display = 'none';
        }
        if (postrunTimer) {
            clearInterval(postrunTimer);
            postrunTimer = null;
        }
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
    if (data.temp1_pin !== undefined && temp1PinEl) {
        temp1PinEl.textContent = data.temp1_pin;
    }
    if (data.temp2_pin !== undefined && temp2PinEl) {
        temp2PinEl.textContent = data.temp2_pin;
    }
    if (data.temp1_pin !== undefined && temp1PinSettingEl) {
        temp1PinSettingEl.textContent = data.temp1_pin;
    }
    if (data.temp2_pin !== undefined && temp2PinSettingEl) {
        temp2PinSettingEl.textContent = data.temp2_pin;
    }
    if (data.swap_sensors !== undefined && swapToggle) {
        swapToggle.checked = data.swap_sensors;
    }
    if (data.output_pct !== undefined) {
        outputEl.textContent = Number(data.output_pct).toFixed(1);
    }
    if (data.mode !== undefined) {
        modeEl.textContent = data.mode;
        const manual = data.mode === 'manual';
        modeToggle.checked = manual;
        manualOutputForm.style.display = manual ? 'block' : 'none';
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
    if (data.alarm_percent !== undefined) {
        alarmOutputInput.placeholder = Number(data.alarm_percent).toFixed(0);
    }
    if (data.wiper_min !== undefined) {
        minOutputInput.placeholder = Number(data.wiper_min).toFixed(0);
    }
    if (data.postrun_seconds !== undefined) {
        postrunInput.placeholder = Number(data.postrun_seconds).toFixed(0);
    }
    if (data.manual_percent !== undefined) {
        manualOutputInput.placeholder = Number(data.manual_percent).toFixed(0);
    }
    if (data.thermocouple_type !== undefined && tcTypeSelect) {
        tcTypeSelect.value = data.thermocouple_type;
    }
    if (data.postrun_remaining !== undefined) {
        updatePostrunCountdown(Math.max(0, Math.round(data.postrun_remaining)));
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
        data.output_pct !== undefined
    ) {
        labels.push(new Date().toLocaleTimeString());
        temp1Data.push(data.temperature1 === null ? null : parseFloat(data.temperature1));
        temp2Data.push(data.temperature2 === null ? null : parseFloat(data.temperature2));
        outputData.push(parseFloat(data.output_pct));
        if (labels.length > maxPoints) {
            labels.shift();
            temp1Data.shift();
            temp2Data.shift();
            outputData.shift();
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

manualOutputForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(manualOutputInput.value);
    if (!isNaN(value)) {
        socket.emit('set_manual_percent', { value });
        manualOutputInput.value = '';
        showFeedback('manualFeedback');
    }
});

alarmOutputForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(alarmOutputInput.value);
    if (!isNaN(value)) {
        socket.emit('set_alarm_percent', { value });
        alarmOutputInput.value = '';
        showFeedback('alarmPwmFeedback');
    }
});

minOutputForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(minOutputInput.value);
    if (!isNaN(value)) {
        socket.emit('set_wiper_min', { value });
        minOutputInput.value = '';
        showFeedback('minOutputFeedback');
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
    manualOutputForm.style.display = modeToggle.checked ? 'block' : 'none';
});

if (swapToggle) {
    swapToggle.addEventListener('change', () => {
        socket.emit('set_swap_sensors', { value: swapToggle.checked });
    });
}

if (tcTypeSelect) {
    tcTypeSelect.addEventListener('change', () => {
        socket.emit('set_thermocouple_type', { value: tcTypeSelect.value });
        showFeedback('tcTypeFeedback');
    });
}

// Listen for system state updates to adjust header color
socket.on('system_state', data => {
    if (!mainHeader) return;
    if (data.alarm_active === true) {
        mainHeader.style.backgroundColor = '#cc0000';
    } else if (data.alarm_active === false) {
        mainHeader.style.backgroundColor = '#0077cc';
    }
});

function addLogRow(entry, prepend = false) {
    if (!logContainer) return;
    const tr = document.createElement('tr');
    const level = (entry.level || '').toLowerCase();
    if (level) tr.classList.add(`log-${level}`);

    const cells = [
        entry.time || '',
        entry.level || '',
        entry.name || '',
        entry.sensor_addr || '',
        entry.attempt || '',
        entry.dt_ms || '',
        entry.status || '',
        entry.temp_hot ?? '',
        entry.temp_cold ?? '',
        entry.delta ?? '',
    ];

    cells.forEach(val => {
        const td = document.createElement('td');
        td.textContent = val;
        tr.appendChild(td);
    });

    const msgTd = document.createElement('td');
    msgTd.classList.add('log-message');
    const message = entry.message || '';
    msgTd.textContent = message;
    msgTd.title = message;
    tr.appendChild(msgTd);

    if (prepend) {
        logContainer.prepend(tr);
    } else {
        logContainer.appendChild(tr);
    }

    while (logContainer.children.length > 200) {
        logContainer.removeChild(logContainer.lastChild);
    }

    if (prepend && logWrapper && logWrapper.scrollTop === 0) {
        logWrapper.scrollTop = 0;
    }
}

socket.on('logs_update', logs => {
    if (!logContainer) return;
    logContainer.innerHTML = '';
    logs
        .sort((a, b) => new Date(b.time) - new Date(a.time))
        .forEach(entry => addLogRow(entry));
});

socket.on('log_entry', entry => {
    addLogRow(entry, true);
});

if (scanBtn) {
    scanBtn.addEventListener('click', () => socket.emit('scan_i2c'));
}
if (testBtn) {
    testBtn.addEventListener('click', () => socket.emit('test_measure'));
}

socket.on('scan_result', data => {
    console.log('scan', data);
});
socket.on('test_measure_result', data => {
    console.log('test', data);
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

