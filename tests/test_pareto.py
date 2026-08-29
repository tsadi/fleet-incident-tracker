from fleet_incident_tracker.events import Event
from fleet_incident_tracker.pareto import pareto_categories


def test_pareto_ranks_and_cumulates_correctly():
    events = (
        [Event("2026-01-01", "DR-1", "incident", "intersection_conflict", "minor")] * 7
        + [Event("2026-01-01", "DR-1", "incident", "curb_strike", "minor")] * 4
        + [Event("2026-01-01", "DR-1", "incident", "pedestrian_proximity", "minor")] * 3
        + [Event("2026-01-01", "DR-1", "near_miss", "tip_over", "n/a")] * 100  # near-misses excluded
    )
    rows = pareto_categories(events)

    assert [r.category for r in rows] == ["intersection_conflict", "curb_strike", "pedestrian_proximity"]
    assert rows[0].count == 7
    assert rows[0].pct_of_total == 50.0  # 7/14
    assert rows[-1].cumulative_pct == 100.0


def test_pareto_empty_incidents_returns_empty_list():
    assert pareto_categories([]) == []
