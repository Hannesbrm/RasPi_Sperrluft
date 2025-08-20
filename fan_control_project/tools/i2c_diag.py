"""Simple diagnostic CLI for MCP9600 sensors."""

from __future__ import annotations

import argparse
import sys
import time

from controller.sensor_reader import SensorReader
from config import load_config
from config.logging_config import logger


def main() -> int:
    parser = argparse.ArgumentParser(description="I2C diagnostic tool")
    parser.add_argument("addresses", nargs="*", help="sensor addresses in hex")
    args = parser.parse_args()

    cfg = load_config()
    addresses = args.addresses or cfg.get("sensor_addresses", [])
    mcp_params = cfg.get("mcp9600", {})

    reader = SensorReader(addresses, mcp_params=mcp_params)
    found = reader.scan_bus()
    logger.info("Scan: %s", found)

    start = time.perf_counter()
    data = reader.read_all()
    dt_ms = int((time.perf_counter() - start) * 1000)
    logger.info("Messdauer %d ms", dt_ms)
    for addr, entry in data.items():
        logger.info(
            "%s: status=%s hot=%s cold=%s delta=%s",
            addr,
            entry.get("status"),
            entry.get("temperature"),
            entry.get("ambient"),
            entry.get("delta"),
        )

    missing = [a for a in addresses if a not in found]
    return 1 if missing else 0


if __name__ == "__main__":  # pragma: no cover - CLI execution
    sys.exit(main())
