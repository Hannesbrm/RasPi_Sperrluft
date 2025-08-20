"""Tests for the MCP9600 sensor_reader module."""

from controller.sensor_reader import SensorReader


def mcp_factory(
    data: dict[int, float],
    fail: set[int] | None = None,
    error: set[int] | None = None,
) -> type:
    """Create a fake MCP9600 class with predefined behaviour."""

    fail = fail or set()
    error = error or set()

    class FakeMCP:
        def __init__(self, _i2c: object, *, address: int) -> None:  # noqa: D401 - simple init
            if address in fail:
                raise OSError("No device")
            self.address = address

        @property
        def temperature(self) -> float:
            if self.address in fail:
                raise OSError("No device")
            if self.address in error:
                raise ValueError("bad read")
            return data.get(self.address, 0.0)

    return FakeMCP


def test_read_temperature() -> None:
    cls = mcp_factory({0x66: 21.5})
    reader = SensorReader(["0x66"], i2c=object(), mcp_cls=cls)
    assert reader.read_temperature(0) == 21.5


def test_read_all_missing_sensor() -> None:
    cls = mcp_factory({0x66: 21.5}, fail={0x67})
    reader = SensorReader(["0x66", "0x67"], i2c=object(), mcp_cls=cls)
    result = reader.read_all()
    assert result["0x66"]["temperature"] == 21.5
    assert result["0x67"]["temperature"] is None
    assert result["0x67"]["status"] == "not_found"


def test_read_temperature_invalid_index_and_missing() -> None:
    cls = mcp_factory({0x66: 20.0}, fail={0x67})
    reader = SensorReader(["0x66", "0x67"], i2c=object(), mcp_cls=cls)
    assert reader.read_temperature(5) is None
    assert reader.read_temperature(1) is None


def test_sensor_error_handling() -> None:
    cls = mcp_factory({}, error={0x66})
    reader = SensorReader(["0x66"], i2c=object(), mcp_cls=cls)
    result = reader.read_all()
    assert result["0x66"]["temperature"] is None
    assert result["0x66"]["status"] == "error"
