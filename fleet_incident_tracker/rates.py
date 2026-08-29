"""Rate statistics: incidents per 1,000 operating hours, near-miss ratio,
and per-unit rate ranking.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .events import Event, incidents, near_misses


def rate_per_1000_hours(count: int, total_operating_hours: float) -> float | None:
    """Events per 1,000 operating hours. None if there's no exposure to
    normalize against (rather than silently returning 0 or dividing by
    zero)."""
    if total_operating_hours <= 0:
        return None
    return count / total_operating_hours * 1000.0


@dataclass(frozen=True)
class FleetRateSummary:
    incident_count: int
    near_miss_count: int
    total_operating_hours: float
    incident_rate_per_1000h: float | None
    near_miss_rate_per_1000h: float | None
    near_miss_to_incident_ratio: float | None  # descriptive only -- see README


def fleet_rate_summary(events: list[Event], total_operating_hours: float) -> FleetRateSummary:
    inc = incidents(events)
    nm = near_misses(events)
    ratio = (len(nm) / len(inc)) if inc else None
    return FleetRateSummary(
        incident_count=len(inc),
        near_miss_count=len(nm),
        total_operating_hours=total_operating_hours,
        incident_rate_per_1000h=rate_per_1000_hours(len(inc), total_operating_hours),
        near_miss_rate_per_1000h=rate_per_1000_hours(len(nm), total_operating_hours),
        near_miss_to_incident_ratio=ratio,
    )


@dataclass(frozen=True)
class UnitRate:
    unit_id: str
    incident_count: int
    operating_hours: float
    rate_per_1000h: float | None


def per_unit_rates(events: list[Event], hours_by_unit: dict[str, float]) -> list[UnitRate]:
    """Incident rate per unit, ranked worst (highest rate) first.

    Units with zero recorded operating hours are still listed (with
    rate_per_1000h=None) rather than silently dropped -- a unit with
    incidents but no logged hours is a data-quality problem worth
    surfacing, not hiding.
    """
    counts = Counter(e.unit_id for e in incidents(events))
    all_units = set(counts) | set(hours_by_unit)

    result = []
    for unit_id in all_units:
        count = counts.get(unit_id, 0)
        unit_hours = hours_by_unit.get(unit_id, 0.0)
        result.append(
            UnitRate(
                unit_id=unit_id,
                incident_count=count,
                operating_hours=unit_hours,
                rate_per_1000h=rate_per_1000_hours(count, unit_hours),
            )
        )

    result.sort(key=lambda u: (u.rate_per_1000h is None, -(u.rate_per_1000h or 0.0)))
    return result
