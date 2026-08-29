from __future__ import annotations

import argparse
import sys
from collections import Counter

from .control_chart import u_chart
from .events import load_events
from .hours import hours_by_period, hours_by_unit, load_hours, total_hours
from .pareto import pareto_categories
from .rates import fleet_rate_summary, per_unit_rates
from .report import render_control_chart_plot, render_markdown_report


def _cmd_report(args: argparse.Namespace) -> int:
    events = load_events(args.events)
    hours_records = load_hours(args.hours)

    hours_total = total_hours(hours_records)
    summary = fleet_rate_summary(events, hours_total)

    unit_rates = per_unit_rates(events, hours_by_unit(hours_records))

    incident_counts_by_period = Counter(e.period for e in events if e.event_type == "incident")
    control_points = u_chart(dict(incident_counts_by_period), hours_by_period(hours_records))

    pareto_rows = pareto_categories(events)

    report_md = render_markdown_report(summary, unit_rates, control_points, pareto_rows, title=args.title)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"Report written to {args.out}")
    else:
        print(report_md)

    if args.plot:
        render_control_chart_plot(control_points, args.plot)
        print(f"Control chart written to {args.plot}")

    flagged = [pt for pt in control_points if pt.out_of_control]
    print(
        f"\n{summary.incident_count} incidents, {summary.near_miss_count} near-misses, "
        f"{len(flagged)} period(s) out of control.",
        file=sys.stderr,
    )
    return 1 if flagged else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fleet-incident-tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    p_report = sub.add_parser("report", help="Generate the fleet safety statistics report.")
    p_report.add_argument("--events", required=True, help="Events CSV path (incidents + near-misses)")
    p_report.add_argument("--hours", required=True, help="Operating-hours CSV path")
    p_report.add_argument("--out", help="Write markdown report to this path (default: stdout)")
    p_report.add_argument("--plot", help="Write a u-chart PNG to this path (requires matplotlib)")
    p_report.add_argument("--title", default="Fleet Incident Report", help="Report title")
    p_report.set_defaults(func=_cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
