from dataclasses import dataclass


@dataclass
class SensorInfo:
    """Describe a connected temperature sensor."""

    rom_id: str
    pin: str
