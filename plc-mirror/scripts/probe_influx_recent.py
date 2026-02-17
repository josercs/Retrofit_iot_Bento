"""Probe recent InfluxDB points for the OEE dashboard metrics.

This is intentionally tiny and dependency-free (uses requests).

Usage (PowerShell):
  python plc-mirror/scripts/probe_influx_recent.py

You can override env vars:
  INFLUX_URL (default http://localhost:8086)
  INFLUX_ORG (default planta)
  INFLUX_TOKEN (default empty)
  INFLUX_BUCKET (default processo)
  INFLUX_RANGE (default -30m)

Notes:
- If INFLUX_TOKEN is empty and your Influx requires auth, you'll get 401.
"""

from __future__ import annotations

import os
import sys

import requests


def flux_query(bucket: str, range_start: str) -> str:
    # Returns last points for both schemas:
    # - new: _measurement=prometheus, metric id in tag `name`
    # - legacy: _measurement=s7_db1, metric id in _field
    return f'''
from(bucket: "{bucket}")
  |> range(start: {range_start})
  |> filter(fn: (r) =>
    (r._measurement == "prometheus" and (r.name == "contador_bom" or r.name == "contador_ruim" or r.name == "maquina_ligada")) or
    (r._measurement == "s7_db1" and (r._field == "contador_bom" or r._field == "contador_ruim" or r._field == "maquina_ligada"))
  )
  |> keep(columns: ["_time", "_measurement", "_field", "name", "ip", "_value"])
  |> group(columns: ["_measurement", "_field", "name", "ip"])
  |> last()
'''.strip()


def main() -> int:
    url = os.environ.get("INFLUX_URL", "http://localhost:8086").rstrip("/")
    org = os.environ.get("INFLUX_ORG", "planta")
    token = os.environ.get("INFLUX_TOKEN", "")
    bucket = os.environ.get("INFLUX_BUCKET", "processo")
    range_start = os.environ.get("INFLUX_RANGE", "-30m")

    q = flux_query(bucket=bucket, range_start=range_start)

    headers = {
        "Accept": "application/csv",
        "Content-Type": "application/vnd.flux",
    }
    if token:
        headers["Authorization"] = f"Token {token}"

    resp = requests.post(f"{url}/api/v2/query?org={org}", headers=headers, data=q.encode("utf-8"))
    print("status", resp.status_code)
    print(resp.text[:4000])

    if resp.status_code >= 400:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
