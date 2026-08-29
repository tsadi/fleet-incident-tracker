"""Loading the fleet operating-hours log: hours by period and unit.

Operating hours are the exposure denominator every rate in this package
is normalized against. Without them, a raw incident count tells you
almost nothing -- a fleet that ran twice as many hours would look twice
as "unsafe" on count alone.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

_REQUIRED_COLUMNS = ("period", "unit_id", "operating_hours")


@dataclass(frozen=True)
class HoursRecord:
    period: str  # YYYY-MM
    unit_id: str
    operating_hours: float


def load_hours(path: str | Path) -> list[HoursRecord]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in _REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"hours CSV is missing required columns: {', '.join(missing)}")

        records = []
        for row in reader:
            records.append(
                HoursRecord(
                    period=row["period"].strip(),
                    unit_id=row["unit_id"].strip(),
                    operating_hours=float(row["operating_hours"]),
                )
            )
    return records


def hours_by_period(records: list[HoursRecord]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for r in records:
        totals[r.period] += r.operating_hours
    return dict(totals)


def hours_by_unit(records: list[HoursRecord]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for r in records:
        totals[r.unit_id] += r.operating_hours
    return dict(totals)


def total_hours(records: list[HoursRecord]) -> float:
    return sum(r.operating_hours for r in records)
