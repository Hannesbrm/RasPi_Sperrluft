const socket = io();

const temp1El = document.getElementById('temp1');
const temp2El = document.getElementById('temp2');
const pwmEl = document.getElementById('pwm');
const modeEl = document.getElementById('mode');
const modeSelect = document.getElementById('modeSelect');

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
const manualPwmForm = document.getElementById('manualPwmForm');
manualPwmForm.addEventListener('submit', e => {
    e.preventDefault();
    const value = parseFloat(document.getElementById('manualPwmInput').value);
    if (!isNaN(value)) {
        socket.emit('set_manual_pwm', { value });
        document.getElementById('manualPwmInput').value = '';
    }
});

// change mode
modeSelect.addEventListener('change', e => {
    socket.emit('set_mode', { mode: e.target.value });
});
