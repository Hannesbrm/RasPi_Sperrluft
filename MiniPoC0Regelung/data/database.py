# database.py

import sqlite3

class Database:
    def __init__(self, db_name):
        # Datenbankname speichern und Initialisierung starten
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        # Erstellt notwendige Tabellen, falls sie nicht existieren
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            # Haupttabelle für Messwerte
            c.execute("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_name TEXT,
                    time_since_start REAL,
                    setpoint REAL,
                    input REAL,
                    pwm REAL,
                    flowrate REAL
                )
            """)

            # Index für schnellere Abfragen nach log_name
            c.execute("CREATE INDEX IF NOT EXISTS idx_log_name ON measurements(log_name)")

            # Tabelle für verfügbare Lognamen
            c.execute("""
                CREATE TABLE IF NOT EXISTS log_names (
                    name TEXT PRIMARY KEY
                )
            """)

            # Tabelle zur Speicherung von Systemeinstellungen (z.B. PID-Werte)
            c.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value REAL
                )
            """)

            conn.commit()

    def ensure_connection(self):
        # Stellt sicher, dass eine Datenbankverbindung aufgebaut werden kann
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            self._init_db()

    def insert_measurement(self, log_name, setpoint, input_val, pwm, flowrate, time_since_start):
        # Fügt einen Messwert in die measurements-Tabelle ein
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO measurements (log_name, time_since_start, setpoint, input, pwm, flowrate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (log_name, time_since_start, setpoint, input_val, pwm, flowrate))
            conn.commit()

    def get_logs(self):
        # Gibt alle vorhandenen log_name-Werte zurück
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT log_name FROM measurements")
            return c.fetchall()

    def get_log_data(self, log_name):
        # Holt alle Messdaten zu einem bestimmten Lognamen
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT time_since_start, setpoint, input, pwm, flowrate
                FROM measurements
                WHERE log_name = ?
            """, (log_name,))
            return c.fetchall()

    def delete_log(self, log_name):
        # Löscht alle Messungen eines bestimmten Logs
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM measurements WHERE log_name = ?", (log_name,))
            conn.commit()

    def add_log_name(self, name):
        # Fügt einen neuen Lognamen hinzu, falls noch nicht vorhanden
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO log_names (name) VALUES (?)", (name,))
            conn.commit()

    def get_all_log_names(self):
        # Gibt alle bekannten Lognamen zurück
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM log_names")
            return [row[0] for row in c.fetchall()]

    def delete_log_name(self, name):
        # Entfernt einen Lognamen aus der Verwaltungstabelle
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM log_names WHERE name = ?", (name,))
            conn.commit()

    def create_log(self, log_name):
        # Erstellt eine neue individuelle Log-Tabelle mit Namen log_name
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(f"""
                CREATE TABLE IF NOT EXISTS "{log_name}" (
                    timestamp TEXT,
                    setpoint REAL,
                    input REAL,
                    pwm REAL,
                    flowrate REAL
                )
            """)
            conn.commit()

    # Methoden zur Verwaltung von Systemeinstellungen

    def set_setting(self, key, value):
        # Speichert eine Einstellung unter einem bestimmten Schlüssel
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            """, (key, value))
            conn.commit()

    def get_setting(self, key):
        # Gibt den Wert einer gespeicherten Einstellung zurück
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT value FROM settings WHERE key = ?
            """, (key,))
            row = c.fetchone()
            return row[0] if row else None

    def get_all_settings(self):
        # Gibt alle gespeicherten Einstellungen als Dictionary zurück
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT key, value FROM settings")
            rows = c.fetchall()
            return {key: value for key, value in rows}