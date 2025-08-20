"""Tests for the MCP9600 sensor_reader module."""

from controller.sensor_reader import SensorReader


def mcp_factory(
    data: dict[int, float],
    ambient: dict[int, float] | None = None,
    fail: set[int] | None = None,
    error: set[int] | None = None,
) -> type:
    """Create a fake MCP9600 class with predefined behaviour."""

    fail = fail or set()
    error = error or set()
    ambient = ambient or {}

    class FakeMCP:
        def __init__(self, _i2c: object, *, address: int, tctype: str = "K", tcfilter: int = 0) -> None:  # noqa: D401 - simple init
            if address in fail:
                raise OSError(121, "No device")
            self.address = address
            self.tctype = tctype
            self.tcfilter = tcfilter

        @property
        def temperature(self) -> float:
            if self.address in fail:
                raise OSError(121, "No device")
            if self.address in error:
                raise ValueError("bad read")
            return data.get(self.address, 0.0)

        @property
        def ambient_temperature(self) -> float:
            return ambient.get(self.address, 0.0)

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


def test_retry_then_success(monkeypatch) -> None:
    class FlakyMCP:
        def __init__(self, _i2c: object, *, address: int, tctype: str = "K", tcfilter: int = 0) -> None:
            self.calls = 0

        @property
        def temperature(self) -> float:
            self.calls += 1
            if self.calls == 1:
                raise OSError(121, "Remote IO")
            return 25.0

        @property
        def ambient_temperature(self) -> float:
            return 20.0

    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    reader = SensorReader(["0x66"], i2c=object(), mcp_cls=FlakyMCP, mcp_params={"retries": 2, "backoff_ms": 10})
    result = reader.read_all()
    assert result["0x66"]["temperature"] == 25.0
    assert sleeps == [0.01]


def test_health_and_stale() -> None:
    cls = mcp_factory({0x66: 30.0, 0x67: 30.0})
    reader = SensorReader(["0x66", "0x67"], i2c=object(), mcp_cls=cls, mcp_params={"stale_threshold_count": 2})
    reader.read_all()
    reader.read_all()
    health = reader.health()
    assert health["0x66"]["status"] == "stale"
    assert health["0x67"]["status"] == "stale"


def test_health_mixed() -> None:
    cls = mcp_factory({0x66: 20.0}, fail={0x67})
    reader = SensorReader(["0x66", "0x67"], i2c=object(), mcp_cls=cls)
    reader.read_all()
    health = reader.health()
    assert health["0x66"]["status"] == "ok"
    assert health["0x67"]["status"] == "not_found"
