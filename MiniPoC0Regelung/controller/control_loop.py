# control_loop.py

# Importieren notwendiger Module
import threading
import time
import datetime
import numpy as np
from controller.pid_adapter import PIDAdapter
from controller.pwm_output import PWMOutput
from controller.sensor_reader import SensorReader
from controller.flow_calculator import FlowCalculator
from collections import deque

# SocketIO-Instanz global setzen
socketio = None

def set_socketio_instance(instance):
    # Setzt die SocketIO-Instanz für spätere Emit-Aufrufe
    global socketio
    socketio = instance

class ControlLoop:
    def __init__(self, db):
        # Initialisierung aller relevanten Variablen und Komponenten
        self.db = db
        self.setpoint = 0.0  # Zieltemperatur
        self.logging = False  # Status der Protokollierung
        self.log_name = None
        self.log_start_time = None
        self.running = True  # Steuert die Hauptschleife
        self.status_messages = []  # Liste der Statusmeldungen
        self.latest_data = None  # Letzte erzeugte Messdaten

        self.mode = "auto"  # Betriebsmodus: "auto" oder "manual"
        self.manual_pwm_value = 0.0  # Manueller PWM-Wert

        # Komponenten initialisieren
        self.reader = SensorReader()
        self.pwm = PWMOutput()
        self.pid = PIDAdapter()
        self.flow = FlowCalculator()

        # PID-Werte aus Datenbank laden
        self.load_pid_from_db()

        # Historie der letzten Temperaturmessungen (für Ø & Trend)
        self.input_history = deque(maxlen=60)

        # Temperaturmessung aktiv ja/nein
        self.temp_probe_active = False
        self.temp_probe_values = []

        # Start der Regelungsschleife in separatem Thread
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.daemon = True
        self.thread.start()

        print("[DEBUG] ControlLoop-Konstruktor aufgerufen", self)

    def load_pid_from_db(self):
        """Lädt gespeicherte PID-Parameter aus der Datenbank."""
        kp = self.db.get_setting("kp")
        ki = self.db.get_setting("ki")
        kd = self.db.get_setting("kd")
        if kp is not None and ki is not None and kd is not None:
            self.pid.set_parameters(kp, ki, kd)
            print(f"[DEBUG] PID-Parameter geladen: Kp={kp}, Ki={ki}, Kd={kd}")
        else:
            print("[DEBUG] Keine gespeicherten PID-Parameter gefunden, Standardwerte werden verwendet.")

    def save_pid_to_db(self, kp, ki, kd):
        """Speichert aktuelle PID-Parameter in der Datenbank."""
        self.db.set_setting("kp", kp)
        self.db.set_setting("ki", ki)
        self.db.set_setting("kd", kd)
        print(f"[DEBUG] PID-Parameter gespeichert: Kp={kp}, Ki={ki}, Kd={kd}")

    def update(self):
        # 🌡️ Temperaturwert einlesen (Istwert)
        input_value = self.reader.read_temperature()

        # ❌ Fehlerfall: Kein gültiger Sensorwert
        if input_value is None:
            self.add_status_message("Kein gültiger Temperaturwert verfügbar – PID-Regelung übersprungen.")
            return self.latest_data if self.latest_data else {}

        # 🧮 PWM-Wert berechnen und setzen
        if self.mode == "manual":
            pwm_value = self.manual_pwm_value
        else:
            # PID-Regelung aktiv – berechnet den Stellwert basierend auf Soll- und Istwert
            pwm_value = self.pid.update(self.setpoint, input_value)

        self.pwm.set_pwm_percent(None, pwm_value)

        # 💨 Volumenstrom berechnen basierend auf PWM-Wert
        flowrate = self.flow.get_flow(pwm_value)

        # 📊 Temperaturhistorie aktualisieren
        self.input_history.append(input_value)

        # 🧮 Gleitender Mittelwert der letzten Temperaturwerte
        avg_input = round(sum(self.input_history) / len(self.input_history), 2) if self.input_history else None

        # 📈 Trendberechnung: Temperaturanstieg, -abfall oder konstant?
        if len(self.input_history) >= 10:
            x = np.arange(len(self.input_history))
            y = np.array(self.input_history)
            slope, _ = np.polyfit(x, y, 1)

            if abs(slope) < 0.005:
                trend_arrow = "→"
            elif slope > 0:
                trend_arrow = "↑"
            else:
                trend_arrow = "↓"
        else:
            trend_arrow = "?"

        # 🔬 Aktive Temperaturmessung (z.B. für Min/Max/Ø Anzeige)
        if self.temp_probe_active:
            self.temp_probe_values.append(input_value)

            probe_min = round(min(self.temp_probe_values), 2)
            probe_max = round(max(self.temp_probe_values), 2)
            probe_avg = round(sum(self.temp_probe_values) / len(self.temp_probe_values), 2)

            socketio.emit("temperature_probe_update", {
                "min": probe_min,
                "max": probe_max,
                "avg": probe_avg,
                "count": len(self.temp_probe_values)
            })

        # 📦 PID-Parameter auslesen (für Webanzeige)
        params = self.pid.get_parameters()
        kp = params["kp"]
        ki = params["ki"]
        kd = params["kd"]

        # 📤 Datenpaket zusammenstellen
        data = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "setpoint": round(self.setpoint, 2),
            "input": round(input_value, 2),
            "pwm": round(pwm_value, 2),
            "flowrate": round(flowrate, 2),
            "kp": round(kp, 4),
            "ki": round(ki, 4),
            "kd": round(kd, 4),
            "logging": self.logging,
            "avg_input": avg_input,
            "input_trend_arrow": trend_arrow,
        }

        # 💾 Letzten Datenzustand speichern (für Web-Frontend)
        self.latest_data = data
        return data

    def run_loop(self):
        # Hauptregelungsschleife
        last_save_time = time.time()
        save_interval = 0.5  # Wie oft Messdaten gespeichert werden

        while self.running:
            try:
                data = self.update()  # Messdaten und Regelung durchführen

                now = time.time()

                # Daten speichern, wenn Logging aktiv ist
                if self.logging and self.log_name and (now - last_save_time) >= save_interval:
                    time_diff = round((datetime.datetime.now() - self.log_start_time).total_seconds(), 1)
                    self.db.insert_measurement(
                        self.log_name,
                        data["setpoint"],
                        data["input"],
                        data["pwm"],
                        data["flowrate"],
                        time_diff
                    )
                    last_save_time = now
            except Exception as e:
                self.add_status_message(f"Fehler in der Regelungsschleife: {e}")

            time.sleep(0.1)  # kurze Pause zur Entlastung der CPU

    def start_logging(self, name):
        # Startet die Protokollierung mit gegebenem Lognamen
        self.logging = True
        self.log_name = name
        self.log_start_time = datetime.datetime.now()
        self.add_status_message(f"Protokollierung gestartet: {name}")

    def stop_logging(self):
        # Stoppt die aktuelle Protokollierung
        self.logging = False
        self.add_status_message("Protokollierung gestoppt")

    def start_temperature_probe(self):
        # Startet manuelle Temperaturmessung zur Analyse
        self.temp_probe_active = True
        self.temp_probe_values.clear()
        self.add_status_message("Temperaturmessung gestartet.")

    def stop_temperature_probe(self):
        # Stoppt die manuelle Temperaturmessung
        self.temp_probe_active = False
        self.temp_probe_values.clear()
        self.add_status_message("Temperaturmessung gestoppt.")

    def set_setpoint(self, value):
        # Setzt neuen Sollwert und setzt den PID-Regler zurück
        self.setpoint = value
        self.pid.reset()
        self.add_status_message(f"Neuer Sollwert: {value} °C")

    def set_pid(self, kp, ki, kd):
        # Setzt neue PID-Parameter und speichert sie
        self.pid.set_parameters(kp, ki, kd)
        self.save_pid_to_db(kp, ki, kd)
        self.add_status_message(f"Neue PID-Parameter: Kp={kp}, Ki={ki}, D={kd}")

    def set_mode(self, mode):
        # Ändert den Modus zwischen automatisch und manuell
        if mode in ["auto", "manual"]:
            self.mode = mode
            self.add_status_message(f"Modus geändert: {mode}")

    def set_manual_pwm(self, value):
        # Setzt den manuellen PWM-Wert (nur im manuellen Modus aktiv)
        value = max(0, min(100, value))  # Begrenzung auf gültigen Bereich
        self.manual_pwm_value = value
        self.add_status_message(f"Manueller PWM-Wert gesetzt: {value}%")

    def shutdown(self):
        # Beendet die Schleife und deaktiviert die PWM-Ausgabe
        self.running = False
        self.pwm.set_pwm_percent(None, 0)
        self.pwm.shutdown()

    def add_status_message(self, message):
        # Fügt eine neue Statusmeldung mit Zeitstempel hinzu
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {"timestamp": timestamp, "message": message}

        self.status_messages.append(entry)
        if len(self.status_messages) > 20:
            self.status_messages.pop(0)

        if socketio:
            socketio.emit("status_message", entry)

    def get_status_messages(self):
        # Gibt alle aktuellen Statusmeldungen zurück
        return self.status_messages
