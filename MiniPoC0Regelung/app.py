from flask import Flask
from flask_socketio import SocketIO
from data.database import Database
from web.routes import configure_routes
from web.socket_events import configure_socket_events
from controller.control_loop import ControlLoop, set_socketio_instance
import atexit
import threading
import time

# Flask-Anwendung und SocketIO initialisieren
app = Flask(
    __name__,
    template_folder="web/templates",  # HTML-Templates liegen hier
    static_folder="web/static"       # Statische Dateien wie JS/CSS hier
)
app.config['SECRET_KEY'] = 'secret!'  # Schlüssel für sichere Sitzungen
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")  # Echtzeit-Kommunikation mit SocketIO
set_socketio_instance(socketio)  # SocketIO-Instanz global verfügbar machen

# Initialisierung der Datenbank und der Regelungsschleife
db = Database("measurements.db")              # Datenbankdatei für Messungen
control_loop = ControlLoop(db)                # Regelungsschleife mit PID, Sensor, PWM usw.

# Routen für die Web-Oberfläche und SocketIO-Ereignisse registrieren
configure_routes(app, db, control_loop)       # Flask-Routen definieren
configure_socket_events(socketio, control_loop)  # SocketIO-Eventhandler verbinden

# Funktion zur regelmäßigen Übertragung von Statusdaten an den Client
# Wird in einem separaten Thread ausgeführt
def broadcast_status():
    while True:
        if control_loop.latest_data is not None:
            data = dict(control_loop.latest_data)  # Aktuelle Werte kopieren
            data["logging"] = control_loop.logging  # Logging-Status anhängen
            if control_loop.log_start_time:
                data["log_start_time"] = control_loop.log_start_time.isoformat()  # Startzeit formatieren
            socketio.emit("status_update", data)  # Status an alle Clients senden
        time.sleep(0.1)  # 100ms Pause zwischen den Updates

# Hintergrund-Thread zur Statusübertragung starten
status_thread = threading.Thread(target=broadcast_status)
status_thread.daemon = True  # Beendet sich automatisch mit dem Hauptprogramm
status_thread.start()

# Registrierung der Shutdown-Funktion für sauberes Herunterfahren
atexit.register(control_loop.shutdown)

# Startet den Server, wenn das Skript direkt ausgeführt wird
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)  # Start auf Port 5000, von außen erreichbar
