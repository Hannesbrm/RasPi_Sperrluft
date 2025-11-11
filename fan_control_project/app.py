"""Entry point for the fan control application."""

# Use the real sensor reader for the MCP9600 sensors
from controller.sensor_reader import SensorReader
from controller.pid_controller import PIDController
from controller.ds3502_output import FanDS3502Controller, DS3502Config
from controller.control_loop import ControlLoop
from web import server
from config import load_config
from config.logging_config import logger, setup_logging
from models.sensor_info import SensorInfo

setup_logging()


def _system_checks() -> None:
    """Run simple system checks and log the results."""
    import os
    import grp
    import getpass

    if os.path.exists("/dev/i2c-1"):
        logger.info("I2C-Bus verfuegbar")
    else:
        logger.warning("/dev/i2c-1 nicht gefunden")

    user = getpass.getuser()
    groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem or g.gr_gid == os.getgid()]
    if "i2c" in groups:
        logger.info("Benutzer %s in i2c-Gruppe", user)
    else:
        logger.warning("Benutzer %s nicht in i2c-Gruppe", user)

    try:
        with open("/boot/config.txt", "r", encoding="utf-8") as f:
            content = f.read()
        if "w1-gpio" in content:
            logger.warning("1-Wire Overlay aktiv")
        else:
            logger.info("1-Wire Overlay deaktiviert")
    except OSError:
        logger.debug("/boot/config.txt nicht lesbar")


def main() -> None:
    """Initialize all components and start the web server."""
    logger.info("Starte Anwendung")

    # Reuse the global state object from the web server so that updates become
    # visible to connected clients.
    state = server.state

    # Load persisted configuration values
    cfg = load_config()
    logger.debug("Konfiguration geladen: %s", cfg)
    state.setpoint = float(cfg.get("setpoint", 0.0))
    state.alarm_threshold = float(cfg.get("alarm_threshold", 0.0))
    state.manual_percent = float(cfg.get("manual_percent", 0.0))
    state.alarm_percent = float(cfg.get("alarm_percent", 100.0))
    state.kp = float(cfg.get("kp", 1.0))
    state.ki = float(cfg.get("ki", 0.1))
    state.kd = float(cfg.get("kd", 0.0))
    state.postrun_seconds = float(cfg.get("postrun_seconds", 30.0))

    ds_cfg = cfg.get("ds3502", {})
    state.wiper_min = int(ds_cfg.get("wiper_min", 2))
    state.swap_sensors = bool(cfg.get("swap_sensors", False))
    sensor_ids = cfg.get("sensor_addresses", [])
    if not sensor_ids:
        sensor_ids = ["0x66", "0x67"]
        logger.info("Sensorliste aus Konfiguration fehlt, verwende Fallback %s", sensor_ids)
    sensors = [SensorInfo(rom_id=sid, pin="I2C") for sid in sensor_ids]
    mcp_params = dict(cfg.get("mcp9600", {}))
    tc_type = str(mcp_params.get("type", "K")).upper()
    mcp_params["type"] = tc_type
    state.thermocouple_type = tc_type
    sensor_reader = SensorReader(sensor_ids, mcp_params=mcp_params)

    found = sensor_reader.scan_bus()
    logger.info("I2C-Scan gefunden=%s konfiguriert=%s", found, sensor_ids)

    if state.swap_sensors:
        state.temp1_pin = sensors[1].pin
        state.temp2_pin = sensors[0].pin
    else:
        state.temp1_pin = sensors[0].pin
        state.temp2_pin = sensors[1].pin

    # Basic PID controller using parameters from the configuration.
    pid = PIDController(
        setpoint=state.setpoint,
        kp=state.kp,
        ki=state.ki,
        kd=state.kd,
        sample_time=0.5,
    )

    config = DS3502Config(
        address=ds_cfg.get("address", "0x28"),
        invert=bool(ds_cfg.get("invert", False)),
        wiper_min=int(ds_cfg.get("wiper_min", 2)),
        wiper_max=int(ds_cfg.get("wiper_max", 125)),
        slew_rate_pct_per_s=float(ds_cfg.get("slew_rate_pct_per_s", 0.0)),
        startup_percent=float(ds_cfg.get("startup_percent", 0.0)),
        safe_low_on_fault=bool(ds_cfg.get("safe_low_on_fault", True)),
    )
    actuator = FanDS3502Controller(config)
    server.actuator = actuator
    if not actuator.available:
        logger.error("DS3502 nicht erreichbar, Fail-Safe aktiv", extra={"actuator": "ds3502", "addr": hex(config.address)})

    control_loop = ControlLoop(
        state,
        sensor_reader,
        pid,
        actuator,
        sensors=sensors,
        alarm_percent=state.alarm_percent,
    )
    control_loop.start()
    logger.info("Steuerung gestartet")

    server.sensor_reader = sensor_reader

    # Expose PID controller to the web server for runtime updates
    server.pid_controller = pid

    server.main()
    logger.info("Anwendung beendet")


if __name__ == "__main__":
    _system_checks()
    main()

