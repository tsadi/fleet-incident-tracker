import pytest

from fleet_incident_tracker.events import Event
from fleet_incident_tracker.rates import fleet_rate_summary, per_unit_rates, rate_per_1000_hours


def test_rate_per_1000_hours_basic():
    assert rate_per_1000_hours(18, 7200) == pytest.approx(2.5)


def test_rate_per_1000_hours_no_exposure_returns_none():
    assert rate_per_1000_hours(5, 0) is None


def test_fleet_rate_summary_hand_verified():
    events = (
        [Event("2026-01-01", "DR-001", "incident", "curb_strike", "minor")] * 18
        + [Event("2026-01-01", "DR-001", "near_miss", "curb_strike", "n/a")] * 36
    )
    summary = fleet_rate_summary(events, total_operating_hours=7200)

    assert summary.incident_count == 18
    assert summary.near_miss_count == 36
    assert summary.incident_rate_per_1000h == pytest.approx(2.5)
    assert summary.near_miss_rate_per_1000h == pytest.approx(5.0)
    assert summary.near_miss_to_incident_ratio == pytest.approx(2.0)


def test_fleet_rate_summary_with_no_incidents_has_no_ratio():
    events = [Event("2026-01-01", "DR-001", "near_miss", "curb_strike", "n/a")]
    summary = fleet_rate_summary(events, total_operating_hours=1000)
    assert summary.incident_count == 0
    assert summary.near_miss_to_incident_ratio is None


def test_per_unit_rates_ranks_worst_first():
    events = (
        [Event("2026-01-01", "DR-A", "incident", "curb_strike", "minor")] * 7
        + [Event("2026-01-01", "DR-B", "incident", "curb_strike", "minor")] * 2
    )
    hours_by_unit = {"DR-A": 1200, "DR-B": 1200, "DR-C": 1200}
    ranked = per_unit_rates(events, hours_by_unit)

    assert ranked[0].unit_id == "DR-A"
    assert ranked[0].rate_per_1000h == pytest.approx(7 / 1200 * 1000)
    # DR-C had zero incidents and is still listed, not dropped
    assert any(u.unit_id == "DR-C" and u.incident_count == 0 for u in ranked)


def test_per_unit_rates_flags_missing_hours_as_none_not_zero():
    events = [Event("2026-01-01", "DR-X", "incident", "curb_strike", "minor")]
    ranked = per_unit_rates(events, hours_by_unit={})
    assert ranked[0].unit_id == "DR-X"
    assert ranked[0].rate_per_1000h is None
