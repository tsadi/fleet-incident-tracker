"""Pareto ranking of incident categories -- which few categories account
for most of the incidents."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .events import Event, incidents


@dataclass(frozen=True)
class ParetoRow:
    category: str
    count: int
    pct_of_total: float
    cumulative_pct: float


def pareto_categories(events: list[Event]) -> list[ParetoRow]:
    inc = incidents(events)
    total = len(inc)
    counts = Counter(e.category for e in inc)

    rows = []
    cumulative = 0
    for category, count in counts.most_common():
        cumulative += count
        rows.append(
            ParetoRow(
                category=category,
                count=count,
                pct_of_total=(count / total * 100.0) if total else 0.0,
                cumulative_pct=(cumulative / total * 100.0) if total else 0.0,
            )
        )
    return rows
