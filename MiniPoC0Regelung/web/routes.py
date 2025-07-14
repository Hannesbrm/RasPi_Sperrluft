from flask import render_template, request, redirect, url_for, send_file
import io
import csv

# Konfiguriert alle HTTP-Routen der Webanwendung
# app: Flask-Instanz
# db: Datenbankinstanz
# control_loop: Steuerungseinheit mit PID-Regelung, Logging usw.
def configure_routes(app, db, control_loop):

    @app.route("/")
    def index():
        # Startseite rendern mit aktuellem Logging-Status und Messdaten
        return render_template(
            "index.html",
            measurement={},
            logging = control_loop.logging,
            log_name = control_loop.log_name,
            error_message=None,
            log_start_time = control_loop.log_start_time.isoformat() if control_loop.log_start_time else "",
            status_messages=control_loop.get_status_messages()
        )

    @app.route("/logs")
    def logs():
        # Seite zur Anzeige aller gespeicherten Logs
        logs = db.get_logs()
        return render_template("logs.html", logs=logs)

    @app.route("/download/<log_name>")
    def download(log_name):
        # Lädt Log-Daten als CSV-Datei herunter
        rows = db.get_log_data(log_name)

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Zeit", "Sollwert", "Istwert", "PWM", "Volumenstrom"])

        # Umwandlung: Punkt in Komma für deutsche Zahlendarstellung
        converted_rows = [
            [str(round(col, 2)).replace('.', ',') if isinstance(col, float) else col for col in row]
            for row in rows
        ]
        writer.writerows(converted_rows)
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"{log_name}.csv"
        )

    @app.route("/delete/<log_name>", methods=["POST"])
    def delete_log(log_name):
        # Löscht das angegebene Log aus der Datenbank und Liste
        db.delete_log(log_name)
        db.delete_log_name(log_name)
        return redirect(url_for("logs"))
