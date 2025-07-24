"""Dummy SensorReader returning fixed temperature values."""

from typing import List, Dict, Optional


class SensorReader:
    def __init__(self, sensor_ids: List[str]):
        """Initialize with the given sensor IDs."""
        self.sensor_ids = list(sensor_ids)

    def _read_sensor_file(self, device_file: str) -> float:
        """Dummy implementation returning a fixed value."""
        return 25.0

    def read_temperature(self, sensor_index: int) -> Optional[float]:
        """Return a constant temperature for the given sensor index."""
        if not (0 <= sensor_index < len(self.sensor_ids)):
            return None
        # Each sensor gets a slightly different value for realism
        return 25.0 + sensor_index

    def read_all(self) -> Dict[str, Dict[str, Optional[float] | str]]:
        """Return temperatures for all configured sensors with status."""
        return {
            sensor_id: {"temperature": self.read_temperature(idx), "status": "ok"}
            for idx, sensor_id in enumerate(self.sensor_ids)
        }
