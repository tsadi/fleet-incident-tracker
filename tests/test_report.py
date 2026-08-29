from fleet_incident_tracker.control_chart import u_chart
from fleet_incident_tracker.events import Event
from fleet_incident_tracker.pareto import pareto_categories
from fleet_incident_tracker.rates import fleet_rate_summary, per_unit_rates
from fleet_incident_tracker.report import render_markdown_report


def test_report_contains_expected_sections_and_flags_spike():
    # Six quiet baseline months (1 incident each on DR-2) plus an April
    # spike (9 incidents on DR-1) -- enough baseline data for the spike
    # to actually exceed the u-chart's UCL. See test_control_chart.py
    # for the equivalent hand-verified numbers.
    quiet_months = ["2026-01", "2026-02", "2026-03", "2026-05", "2026-06"]
    events = [
        Event(f"2026-04-{d:02d}", "DR-1", "incident", "intersection_conflict", "moderate")
        for d in range(1, 10)
    ]
    for i, month in enumerate(quiet_months, start=1):
        events.append(Event(f"{month}-05", "DR-2", "incident", "curb_strike", "minor"))
    events += [Event("2026-01-06", "DR-2", "near_miss", "curb_strike", "n/a")] * 3

    hours_by_unit_map = {"DR-1": 1200, "DR-2": 1200}
    hours_by_period_map = {m: 1200 for m in quiet_months + ["2026-04"]}

    summary = fleet_rate_summary(events, total_operating_hours=sum(hours_by_period_map.values()))
    unit_rates = per_unit_rates(events, hours_by_unit_map)
    from collections import Counter

    counts = Counter(e.period for e in events if e.event_type == "incident")
    points = u_chart(dict(counts), hours_by_period_map)
    pareto_rows = pareto_categories(events)

    report = render_markdown_report(summary, unit_rates, points, pareto_rows, title="Test Fleet Report")

    assert "# Test Fleet Report" in report
    assert "Incidents: 14" in report
    assert "OUT OF CONTROL" in report
    assert "intersection_conflict" in report
    assert "DR-1" in report
