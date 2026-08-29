from collections import Counter
from pathlib import Path

import pytest

from fleet_incident_tracker.control_chart import u_chart
from fleet_incident_tracker.events import load_events
from fleet_incident_tracker.hours import hours_by_period, hours_by_unit, load_hours, total_hours
from fleet_incident_tracker.pareto import pareto_categories
from fleet_incident_tracker.rates import fleet_rate_summary, per_unit_rates

ROOT = Path(__file__).resolve().parents[1]


def _load():
    events = load_events(ROOT / "sample_data" / "events.csv")
    hours_records = load_hours(ROOT / "sample_data" / "hours.csv")
    return events, hours_records


def test_sample_fleet_summary():
    events, hours_records = _load()
    summary = fleet_rate_summary(events, total_hours(hours_records))

    assert summary.incident_count == 18
    assert summary.near_miss_count == 36
    assert summary.total_operating_hours == pytest.approx(7200)
    assert summary.incident_rate_per_1000h == pytest.approx(2.5)
    assert summary.near_miss_to_incident_ratio == pytest.approx(2.0)


def test_sample_u_chart_flags_only_april():
    events, hours_records = _load()
    incident_counts_by_period = Counter(e.period for e in events if e.event_type == "incident")
    points = u_chart(dict(incident_counts_by_period), hours_by_period(hours_records))

    flagged = [p.period for p in points if p.out_of_control]
    assert flagged == ["2026-04"]


def test_sample_pareto_top_category_is_intersection_conflict():
    events, _ = _load()
    rows = pareto_categories(events)
    assert rows[0].category == "intersection_conflict"
    assert rows[0].count == 7


def test_sample_worst_unit_is_dr_004():
    events, hours_records = _load()
    ranked = per_unit_rates(events, hours_by_unit(hours_records))
    assert ranked[0].unit_id == "DR-004"
    assert ranked[0].incident_count == 7
