"""Tests for the sensor_reader module."""

from pathlib import Path

from controller.sensor_reader import SensorReader


def _create_sensor(tmp_path: Path, sensor_id: str, temperature: float) -> None:
    sensor_dir = tmp_path / sensor_id
    sensor_dir.mkdir()
    content = (
        "00 00 00 00 00 00 00 00 00 00 : crc=00 YES\n"
        f"00 00 00 00 00 00 00 00 00 00 t={int(temperature * 1000)}\n"
    )
    (sensor_dir / "w1_slave").write_text(content)


def _create_sensor_custom(
    tmp_path: Path,
    sensor_id: str,
    first_line: str,
    second_line: str,
) -> None:
    sensor_dir = tmp_path / sensor_id
    sensor_dir.mkdir()
    (sensor_dir / "w1_slave").write_text(first_line + "\n" + second_line + "\n")


def test_read_temperature(tmp_path: Path) -> None:
    _create_sensor(tmp_path, "3b-000000000001", 21.5)
    reader = SensorReader(["3b-000000000001"], base_path=tmp_path)
    assert reader.read_temperature(0) == 21.5


def test_read_all_missing_sensor(tmp_path: Path) -> None:
    _create_sensor(tmp_path, "3b-000000000001", 21.5)
    reader = SensorReader(["3b-000000000001", "3b-does-not-exist"], base_path=tmp_path)
    result = reader.read_all()
    assert result["3b-000000000001"]["temperature"] == 21.5
    assert result["3b-does-not-exist"]["temperature"] is None
    assert result["3b-does-not-exist"]["status"] == "not_found"


def test_read_temperature_invalid_index_and_missing(tmp_path: Path) -> None:
    _create_sensor(tmp_path, "3b-1", 20.0)
    reader = SensorReader(["3b-1", "3b-2"], base_path=tmp_path)
    assert reader.read_temperature(5) is None
    assert reader.read_temperature(1) is None


def test_sensor_status_bits_and_errors(tmp_path: Path) -> None:
    base_first = "00 00 00 00 00 00 00 00 00 00 : crc=00 YES"
    second_template = "00 00 {status:02x} 00 00 00 00 00 00 00 t=21000"
    _create_sensor_custom(
        tmp_path,
        "s1",
        base_first,
        second_template.format(status=0x01),
    )
    _create_sensor_custom(
        tmp_path,
        "s2",
        base_first,
        second_template.format(status=0x02),
    )
    _create_sensor_custom(
        tmp_path,
        "s3",
        base_first,
        second_template.format(status=0x04),
    )
    reader = SensorReader(["s1", "s2", "s3"], base_path=tmp_path)
    result = reader.read_all()
    assert result["s1"]["status"] == "open_circuit"
    assert result["s2"]["status"] == "short_gnd"
    assert result["s3"]["status"] == "short_vcc"


def test_sensor_crc_and_missing_temperature(tmp_path: Path) -> None:
    _create_sensor_custom(
        tmp_path,
        "s1",
        "00 00 00 00 00 00 00 00 00 00 : crc=00 NO",
        "00 00 00 00 00 00 00 00 00 00 t=21000",
    )
    _create_sensor_custom(
        tmp_path,
        "s2",
        "00 00 00 00 00 00 00 00 00 00 : crc=00 YES",
        "00 00 00 00 00 00 00 00 00 00",
    )
    reader = SensorReader(["s1", "s2"], base_path=tmp_path)
    res = reader.read_all()
    assert res["s1"]["temperature"] is None and res["s1"]["status"] == "error"
    assert res["s2"]["temperature"] is None and res["s2"]["status"] == "error"
