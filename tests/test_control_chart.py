import pytest

from fleet_incident_tracker.control_chart import u_chart


def test_u_chart_hand_verified_with_one_spike():
    # 6 equal-exposure periods, 1200 hours each (7200 total).
    # counts: 2,1,3,9,2,1 -> total 18, ubar = 18/7200 = 0.0025/hr = 2.5/1000h
    # sigma = sqrt(ubar/1200) = sqrt(2.0833e-6) = 0.00144338/hr
    # UCL = (0.0025 + 3*0.00144338)*1000 = 6.83013 /1000h
    # LCL = max(0, 0.0025 - 3*0.00144338) = 0 (clamped)
    counts = {
        "2026-01": 2,
        "2026-02": 1,
        "2026-03": 3,
        "2026-04": 9,
        "2026-05": 2,
        "2026-06": 1,
    }
    hours = {p: 1200 for p in counts}

    points = u_chart(counts, hours)
    by_period = {p.period: p for p in points}

    assert by_period["2026-01"].rate_per_1000h == pytest.approx(1.6667, abs=1e-3)
    assert by_period["2026-04"].rate_per_1000h == pytest.approx(7.5)
    assert by_period["2026-04"].center_per_1000h == pytest.approx(2.5)
    assert by_period["2026-04"].ucl_per_1000h == pytest.approx(6.83013, abs=1e-3)
    assert by_period["2026-04"].lcl_per_1000h == pytest.approx(0.0)

    flagged = [p.period for p in points if p.out_of_control]
    assert flagged == ["2026-04"]


def test_u_chart_unequal_exposure_widens_limits_for_low_exposure_period():
    # A period with much less exposure should get wider control limits.
    counts = {"2026-01": 5, "2026-02": 5}
    hours = {"2026-01": 1000, "2026-02": 100}

    points = u_chart(counts, hours)
    by_period = {p.period: p for p in points}

    width_jan = by_period["2026-01"].ucl_per_1000h - by_period["2026-01"].lcl_per_1000h
    width_feb = by_period["2026-02"].ucl_per_1000h - by_period["2026-02"].lcl_per_1000h
    assert width_feb > width_jan


def test_u_chart_rejects_period_with_zero_hours():
    with pytest.raises(ValueError):
        u_chart({"2026-01": 3}, {"2026-01": 0})
