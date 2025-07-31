"""Entry point for the fan control application."""

# Use the real sensor reader for the MAX31850K sensors
from controller.sensor_reader import SensorReader
from controller.sensor_reader_mcp9600 import SensorReaderMCP9600
from controller.pid_controller import PIDController
from controller.pwm_output import FanPWMController
from controller.control_loop import ControlLoop
from web import server
from config import load_config, load_hardware_config
from config.logging_config import logger

# Sensor mapping will be constructed based on config.yaml
sensor_mapping: dict[str, str] = {}


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
    state.manual_pwm = float(cfg.get("manual_pwm", 0.0))
    state.alarm_pwm = float(cfg.get("alarm_pwm", 100.0))
    state.min_pwm = float(cfg.get("min_pwm", 20.0))
    pwm_pin = int(cfg.get("pwm_pin", 12))
    state.kp = float(cfg.get("kp", 1.0))
    state.ki = float(cfg.get("ki", 0.1))
    state.kd = float(cfg.get("kd", 0.0))
    state.postrun_seconds = float(cfg.get("postrun_seconds", 30.0))

    # Read hardware configuration selecting sensor type and identifiers
    hw_cfg = load_hardware_config()
    sensor_type = str(hw_cfg.get("sensor_type", "max31850")).lower()

    if sensor_type == "max31850":
        ids_dict = hw_cfg.get("sensor_ids", {}) or {}
        if not isinstance(ids_dict, dict):
            ids_dict = {}
        sensor_mapping.update(ids_dict)
        sensor_reader = SensorReader(list(sensor_mapping.values()))
    elif sensor_type == "mcp9600":
        addresses = hw_cfg.get("sensor_addresses")
        if not isinstance(addresses, list) or not addresses:
            addresses = [0x60]
        int_addrs = []
        for addr in addresses:
            try:
                int_addrs.append(int(addr, 0))
            except Exception:
                logger.warning("Ungueltige Adresse %s in config.yaml", addr)
        if not int_addrs:
            int_addrs = [0x60]
        sensor_reader = SensorReaderMCP9600(int_addrs)
        for idx, addr in enumerate(int_addrs, start=1):
            name = f"mcp_{addr:02x}"
            sensor_mapping[f"temperature{idx}"] = name
    else:
        logger.error("Ungueltiger sensor_type '%s' in config.yaml", sensor_type)
        sensor_reader = SensorReader([])

    # Basic PID controller using parameters from the configuration.
    pid = PIDController(
        setpoint=state.setpoint,
        kp=state.kp,
        ki=state.ki,
        kd=state.kd,
        sample_time=0.5,
    )

    pwm_controller = FanPWMController(pin=pwm_pin, min_pwm=state.min_pwm)

    control_loop = ControlLoop(
        state,
        sensor_reader,
        pid,
        pwm_controller,
        state.alarm_pwm,
        sensor_mapping=sensor_mapping,
    )
    control_loop.start()
    logger.info("Steuerung gestartet")

    # Expose PID controller to the web server for runtime updates
    server.pid_controller = pid

    server.main()
    logger.info("Anwendung beendet")


if __name__ == "__main__":
    main()

