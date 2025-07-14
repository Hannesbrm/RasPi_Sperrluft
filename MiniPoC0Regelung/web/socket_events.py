# socket_events.py

import time
import os
import subprocess
from flask import request

# Funktion zur Registrierung aller SocketIO-Events
# Verbindet die Events mit der übergebenen Kontrollschleife

def configure_socket_events(socketio, control_loop):

    # Sollwert vom Client empfangen und setzen
    @socketio.on("send_setpoint")
    def handle_send_setpoint(data):
        try:
            value = float(data.get("value", 0))
            if value < 0:
                raise ValueError("Sollwert darf nicht negativ sein.")
            control_loop.set_setpoint(value)
        except Exception as e:
            control_loop.add_status_message(f"Fehler beim Setzen des Sollwerts: {e}")

    # PID-Parameter (Kp, Ki, Kd) komplett setzen
    @socketio.on("send_pid")
    def handle_send_pid(data):
        try:
            kp = float(data.get("kp", 0))
            ki = float(data.get("ki", 0))
            kd = float(data.get("kd", 0))
            if any(x < 0 for x in [kp, ki, kd]):
                raise ValueError("PID-Werte dürfen nicht negativ sein.")
            control_loop.set_pid(kp, ki, kd)
        except Exception as e:
            control_loop.add_status_message(f"Fehler beim Setzen der PID-Werte: {e}")

    # Nur Kp-Wert einzeln setzen
    @socketio.on("send_kp")
    def handle_send_kp(data):
        try:
            kp = float(data.get("kp", 0))
            current = control_loop.pid.get_parameters()
            control_loop.set_pid(kp, current['ki'], current['kd'])
        except Exception as e:
            control_loop.add_status_message(f"Fehler beim Setzen von Kp: {e}")

    # Nur Ki-Wert einzeln setzen
    @socketio.on("send_ki")
    def handle_send_ki(data):
        try:
            ki = float(data.get("ki", 0))
            current = control_loop.pid.get_parameters()
            control_loop.set_pid(current['kp'], ki, current['kd'])
        except Exception as e:
            control_loop.add_status_message(f"Fehler beim Setzen von Ki: {e}")

    # Nur Kd-Wert einzeln setzen
    @socketio.on("send_kd")
    def handle_send_kd(data):
        try:
            kd = float(data.get("kd", 0))
            current = control_loop.pid.get_parameters()
            control_loop.set_pid(current['kp'], current['ki'], kd)
        except Exception as e:
            control_loop.add_status_message(f"Fehler beim Setzen von Kd: {e}")

    # Start der Messprotokollierung (Logging)
    @socketio.on("start_logging")
    def handle_start_logging(data):
        try:
            from datetime import datetime
            base = data.get("log_name", "log").strip()
            timestamp = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
            name = f"{base}_{timestamp}"
            control_loop.start_logging(name)
            data = control_loop.update()
            data["logging"] = True
            data["log_start_time"] = control_loop.log_start_time.isoformat()
            socketio.emit("status_update", data)
        except Exception as e:
            control_loop.add_status_message(f"Fehler beim Starten der Protokollierung: {e}")

    # Stopp der Messprotokollierung
    @socketio.on("stop_logging")
    def handle_stop_logging():
        try:
            control_loop.stop_logging()
            data = control_loop.update()
            data["logging"] = False
            socketio.emit("status_update", data)
        except Exception as e:
            control_loop.add_status_message(f"Fehler beim Stoppen der Protokollierung: {e}")

    # Temperaturmessung starten (Min/Max/Ø)
    @socketio.on("start_temperature_probe")
    def handle_start_probe():
        control_loop.start_temperature_probe()

    # Temperaturmessung stoppen
    @socketio.on("stop_temperature_probe")
    def handle_stop_probe():
        control_loop.stop_temperature_probe()

    # Automatik- oder manuellen Modus setzen
    @socketio.on("set_mode")
    def handle_set_mode(data):
        mode = data.get("mode")
        control_loop.set_mode(mode)

    # PWM-Wert im manuellen Modus setzen
    @socketio.on("set_manual_pwm")
    def handle_set_manual_pwm(data):
        try:
            value = float(data.get("value", 0))
            control_loop.set_manual_pwm(value)
        except Exception as e:
            control_loop.add_status_message(f"Fehler beim Setzen des manuellen PWM-Werts: {e}")

    # Alle gespeicherten Statusmeldungen an Client senden
    @socketio.on("request_status_log")
    def handle_request_status_log():
        for entry in control_loop.get_status_messages():
            socketio.emit("status_message", {
                "timestamp": entry["timestamp"],
                "message": entry["message"]
            })

    # Raspberry Pi neustarten (mit sudo)
    @socketio.on("reboot")
    def handle_reboot():
        try:
            control_loop.add_status_message("System wird neu gestartet...")
            subprocess.Popen(["sudo", "reboot"])
        except Exception as e:
            control_loop.add_status_message(f"Neustart fehlgeschlagen: {e}")

    # Bei erfolgreicher Verbindung: Client begrüßen und aktuellen Status senden
    @socketio.on("connect")
    def handle_connect():
        print(f"[SocketIO] Client verbunden: {request.sid}")
        if control_loop.latest_data:
            socketio.emit("status_update", control_loop.latest_data)

    # Bei Trennung des Clients
    @socketio.on("disconnect")
    def handle_disconnect():
        print(f"[SocketIO] Client getrennt: {request.sid}")
