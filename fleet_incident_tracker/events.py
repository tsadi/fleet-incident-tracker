"""Loading the fleet event log: incidents and near-misses."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

_REQUIRED_COLUMNS = ("date", "unit_id", "event_type", "category", "severity")
_VALID_EVENT_TYPES = {"incident", "near_miss"}


@dataclass(frozen=True)
class Event:
    date: str  # YYYY-MM-DD
    unit_id: str
    event_type: str  # "incident" or "near_miss"
    category: str
    severity: str  # "minor" / "moderate" / "major" / "n/a" (near-misses have no realized severity)

    @property
    def period(self) -> str:
        """Month bucket, YYYY-MM, derived from date."""
        return self.date[:7]


def load_events(path: str | Path) -> list[Event]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in _REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"events CSV is missing required columns: {', '.join(missing)}")

        events = []
        for row in reader:
            event_type = row["event_type"].strip()
            if event_type not in _VALID_EVENT_TYPES:
                raise ValueError(
                    f"unknown event_type {event_type!r} on {row['date']} "
                    f"(must be one of {sorted(_VALID_EVENT_TYPES)})"
                )
            events.append(
                Event(
                    date=row["date"].strip(),
                    unit_id=row["unit_id"].strip(),
                    event_type=event_type,
                    category=row["category"].strip(),
                    severity=row["severity"].strip(),
                )
            )
    return events


def incidents(events: list[Event]) -> list[Event]:
    return [e for e in events if e.event_type == "incident"]


def near_misses(events: list[Event]) -> list[Event]:
    return [e for e in events if e.event_type == "near_miss"]
