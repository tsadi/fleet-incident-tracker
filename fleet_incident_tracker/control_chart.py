"""u-chart: an exposure-normalized statistical process control chart for
incident counts by period.

A plain c-chart (constant control limits on raw counts) assumes every
period had the same "area of opportunity" -- the same operating hours.
That assumption breaks the moment fleet size or utilization changes
month to month, which real fleets do constantly. A u-chart instead
control-charts the *rate* (count / exposure) per period, with control
limits that widen or narrow with that period's own exposure -- a
month with fewer operating hours naturally has wider limits, because a
rate estimated from less data is noisier. This is the standard
approach for count data with unequal sample sizes (see e.g. Montgomery,
"Introduction to Statistical Quality Control", ch. 7).

For period i with count y_i and exposure (operating hours) n_i:

    u_i    = y_i / n_i                          (rate, per hour)
    ubar   = sum(y_i) / sum(n_i)                 (center line, per hour)
    UCL_i  = ubar + 3 * sqrt(ubar / n_i)
    LCL_i  = max(0, ubar - 3 * sqrt(ubar / n_i))

A period is "out of control" if its rate falls outside [LCL_i, UCL_i] --
i.e. further from the long-run average than ordinary period-to-period
noise would explain, at roughly a 3-sigma confidence level under the
usual Poisson approximation. That's a statistical flag, not a root
cause -- see README "What this is not".

All rates and limits are reported per 1,000 operating hours for
readability; this is a pure unit change (multiply everything by 1,000),
not a different chart.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PeriodPoint:
    period: str
    count: int
    operating_hours: float
    rate_per_1000h: float
    center_per_1000h: float
    ucl_per_1000h: float
    lcl_per_1000h: float
    out_of_control: bool


def u_chart(counts_by_period: dict[str, int], hours_by_period: dict[str, float]) -> list[PeriodPoint]:
    periods = sorted(set(counts_by_period) | set(hours_by_period))

    total_count = sum(counts_by_period.get(p, 0) for p in periods)
    total_hours = sum(hours_by_period.get(p, 0.0) for p in periods)
    if total_hours <= 0:
        raise ValueError("total operating hours across all periods must be > 0")

    ubar = total_count / total_hours  # per hour

    points = []
    for p in periods:
        count = counts_by_period.get(p, 0)
        period_hours = hours_by_period.get(p, 0.0)
        if period_hours <= 0:
            # No exposure logged for a period that has events is a data
            # problem, not something to silently paper over.
            raise ValueError(f"period {p!r} has zero or missing operating hours")

        rate = count / period_hours  # per hour
        sigma = math.sqrt(ubar / period_hours)
        ucl = ubar + 3 * sigma
        lcl = max(0.0, ubar - 3 * sigma)

        points.append(
            PeriodPoint(
                period=p,
                count=count,
                operating_hours=period_hours,
                rate_per_1000h=rate * 1000,
                center_per_1000h=ubar * 1000,
                ucl_per_1000h=ucl * 1000,
                lcl_per_1000h=lcl * 1000,
                out_of_control=(rate > ucl or rate < lcl),
            )
        )
    return points
