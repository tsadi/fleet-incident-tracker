"""Markdown (and optional plot) reporting."""

from __future__ import annotations

from .control_chart import PeriodPoint
from .pareto import ParetoRow
from .rates import FleetRateSummary, UnitRate


def _fmt_rate(rate: float | None) -> str:
    return f"{rate:.2f}" if rate is not None else "n/a (no hours logged)"


def render_markdown_report(
    summary: FleetRateSummary,
    unit_rates: list[UnitRate],
    control_points: list[PeriodPoint],
    pareto_rows: list[ParetoRow],
    title: str = "Fleet Incident Report",
) -> str:
    lines = [f"# {title}", ""]

    lines.append("## Fleet summary")
    lines.append("")
    lines.append(f"- Operating hours: {summary.total_operating_hours:,.0f}")
    lines.append(f"- Incidents: {summary.incident_count}")
    lines.append(f"- Near-misses: {summary.near_miss_count}")
    lines.append(f"- Incident rate: {_fmt_rate(summary.incident_rate_per_1000h)} per 1,000 operating hours")
    lines.append(f"- Near-miss rate: {_fmt_rate(summary.near_miss_rate_per_1000h)} per 1,000 operating hours")
    if summary.near_miss_to_incident_ratio is not None:
        lines.append(
            f"- Near-miss : incident ratio: {summary.near_miss_to_incident_ratio:.1f} : 1 "
            f"(descriptive only -- see README, this is not a validated predictive ratio)"
        )
    lines.append("")

    lines.append("## Trend (u-chart, exposure-normalized)")
    lines.append("")
    lines.append("| period | count | hours | rate /1000h | center | UCL | LCL | status |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for pt in control_points:
        status = "**OUT OF CONTROL**" if pt.out_of_control else "in control"
        lines.append(
            f"| {pt.period} | {pt.count} | {pt.operating_hours:,.0f} | "
            f"{pt.rate_per_1000h:.2f} | {pt.center_per_1000h:.2f} | "
            f"{pt.ucl_per_1000h:.2f} | {pt.lcl_per_1000h:.2f} | {status} |"
        )
    lines.append("")
    flagged = [pt for pt in control_points if pt.out_of_control]
    if flagged:
        periods_str = ", ".join(pt.period for pt in flagged)
        lines.append(
            f"{len(flagged)} period(s) fall outside the u-chart's 3-sigma band: {periods_str}. "
            f"That means the rate that period is a statistically unusual departure from the "
            f"fleet's own baseline -- not automatically a root cause, and not automatically "
            f"noise either. Investigate what changed that period."
        )
        lines.append("")

    lines.append("## Category breakdown (Pareto)")
    lines.append("")
    lines.append("| category | count | % of incidents | cumulative % |")
    lines.append("|---|---|---|---|")
    for row in pareto_rows:
        lines.append(
            f"| {row.category} | {row.count} | {row.pct_of_total:.1f}% | {row.cumulative_pct:.1f}% |"
        )
    lines.append("")

    lines.append("## Per-unit incident rate (worst first)")
    lines.append("")
    lines.append("| unit | incidents | hours | rate /1000h |")
    lines.append("|---|---|---|---|")
    for u in unit_rates:
        lines.append(f"| {u.unit_id} | {u.incident_count} | {u.operating_hours:,.0f} | {_fmt_rate(u.rate_per_1000h)} |")
    lines.append("")

    return "\n".join(lines)


def render_control_chart_plot(control_points: list[PeriodPoint], out_path: str) -> None:
    """u-chart plot: rate per period with its own (period-specific)
    control limits. Requires matplotlib (`pip install -e ".[viz]"`)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised only without matplotlib
        raise ImportError(
            "render_control_chart_plot requires matplotlib. Install it with: pip install -e \".[viz]\""
        ) from exc

    periods = [pt.period for pt in control_points]
    rates = [pt.rate_per_1000h for pt in control_points]
    ucl = [pt.ucl_per_1000h for pt in control_points]
    lcl = [pt.lcl_per_1000h for pt in control_points]
    center = [pt.center_per_1000h for pt in control_points]
    colors = ["#c0392b" if pt.out_of_control else "#2c7a7b" for pt in control_points]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(periods, center, linestyle="--", color="#4a5568", label="center (ubar)")
    ax.plot(periods, ucl, linestyle=":", color="#c0392b", label="UCL")
    ax.plot(periods, lcl, linestyle=":", color="#c0392b", label="LCL")
    ax.plot(periods, rates, color="#2c7a7b", linewidth=1.5, zorder=2)
    ax.scatter(periods, rates, c=colors, zorder=3)
    ax.set_xlabel("period")
    ax.set_ylabel("incident rate per 1,000 operating hours")
    ax.set_title("Fleet incident u-chart")
    ax.legend()
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
