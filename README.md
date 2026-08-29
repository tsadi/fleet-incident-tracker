# fleet-incident-tracker

Fleet-level safety statistics for robot/AMR operations, built the way an
ops safety review actually needs them: normalized by exposure (operating
hours), not raw counts. Point it at an incident/near-miss log and an
operating-hours log and it computes an incident rate per 1,000 operating
hours, a near-miss ratio, an exposure-normalized trend chart, a category
Pareto, and a per-unit outlier ranking.

```bash
fleet-incident-tracker report \
  --events sample_data/events.csv \
  --hours sample_data/hours.csv
```

Ships with six months of synthetic data for a 6-robot sidewalk delivery
fleet, with one unit and one month deliberately built to be statistical
outliers -- so the trend chart and the per-unit ranking both have
something real to catch.

## Why exposure-normalized, and why a u-chart and not a c-chart

A raw incident count is close to meaningless on its own: a fleet that
ran twice as many hours will rack up roughly twice as many incidents
without being any less safe. Every rate in this tool is count divided
by operating hours.

The trend chart is a **u-chart**, not the more commonly-demoed
**c-chart**. A c-chart's control limits assume every period had equal
exposure -- fine for, say, defects per fixed-size batch, wrong the
moment a fleet's operating hours vary month to month, which real fleets
do constantly (more units added, weather, demand). A u-chart
control-charts the *rate* per period instead, with limits that widen or
narrow with that period's own exposure. `control_chart.py`'s module
docstring has the full derivation. This is standard statistical
process control for count data with unequal sample sizes (see e.g.
Montgomery, *Introduction to Statistical Quality Control*, ch. 7), not
something specific to robotics.

## What "near-miss : incident ratio" is and isn't

The report computes the observed ratio of near-misses to incidents in
your own data. It does **not** invoke Heinrich's 300:29:1 triangle or
any other fixed historical ratio as a predictive law -- that specific
ratio came from one 1930s industrial accident dataset and modern safety
research treats it as descriptive history, not a universal constant.
What's useful here is tracking *your* fleet's own ratio over time and
noticing when it shifts, not comparing it to someone else's number from
a different industry a century ago.

## What this computes

- **Rates**: incidents and near-misses per 1,000 operating hours,
  fleet-wide.
- **Trend**: a u-chart by month, flagging any period whose rate falls
  outside its own 3-sigma band -- a statistical anomaly flag, not a root
  cause.
- **Pareto**: incident categories ranked by frequency with cumulative
  %, to find the few categories driving most of the incidents.
- **Per-unit ranking**: incident rate per robot/vehicle, worst first,
  hours-normalized so a high-utilization unit isn't unfairly flagged
  just for running more.

## What this is *not*

- Not a regulatory recordability determination. What counts as a
  reportable "incident" vs. a "near-miss" is whatever your own
  operational definitions say -- this tool doesn't classify events, it
  only aggregates however you've already classified them.
- Not a causal analysis. An out-of-control month or an outlier unit is
  a flag that something changed relative to the fleet's own baseline --
  it doesn't say what, and a human still has to investigate.
- Not validation of any specific incident-pyramid ratio (see above).
- The sample data is synthetic, built to demonstrate the statistics
  clearly, not real fleet history.

## Install

```bash
pip install -e ".[dev]"        # core + tests
pip install -e ".[dev,viz]"    # + plotting
```

## Data format

`events.csv`: `date,unit_id,event_type,category,severity` -- one row per
incident or near-miss. `event_type` is `incident` or `near_miss`.
`severity` (`minor`/`moderate`/`major`) is only meaningful for
incidents; near-misses use `n/a`.

`hours.csv`: `period,unit_id,operating_hours` -- operating hours per
robot per month (`YYYY-MM`). Every period referenced in `events.csv`
needs a corresponding hours entry, or the report will refuse to compute
a rate for it rather than silently dividing by zero.

## Test

```bash
pytest -v
```

Every rate and control-limit calculation is hand-computed and asserted
with `pytest.approx` -- see the comments in `tests/test_control_chart.py`
and `tests/test_rates.py`.

## Project layout

```
fleet_incident_tracker/
  events.py         loads the incident/near-miss log
  hours.py          loads the operating-hours log, aggregates by period/unit
  rates.py          rate-per-1000-hours, near-miss ratio, per-unit ranking
  control_chart.py  u-chart (exposure-normalized SPC trend)
  pareto.py         category Pareto ranking
  report.py         markdown report + optional matplotlib u-chart plot
  cli.py            `fleet-incident-tracker` command
tests/              hand-verified stats tests + a full sample-data integration test
sample_data/        6 months, 6-unit synthetic fleet log with a built-in outlier month/unit
```
