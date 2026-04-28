"""Chart generation for security metrics."""

from pathlib import Path
from typing import Optional

from .models import MetricReport, TrendPoint


def export_charts(report: MetricReport, output_dir: Path) -> list[Path]:
    """Generate PNG charts from a metric report. Returns list of generated file paths."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError:
        raise ImportError("matplotlib required for charts. Install with: pip install matplotlib")

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    paths.append(_chart_sla_gauge(report, output_dir, plt))
    paths.append(_chart_alert_quality(report, output_dir, plt))
    paths.append(_chart_mttd_mttr(report, output_dir, plt))

    if report.trends:
        paths.append(_chart_trends(report, output_dir, plt))

    plt.close("all")
    return paths


def _chart_sla_gauge(report, output_dir, plt):
    fig, ax = plt.subplots(figsize=(6, 4))
    compliance = report.vuln_sla.sla_compliance_pct
    colors = ["#E60000", "#FFC107", "#28A745"]
    bounds = [0, 70, 85, 100]
    color = colors[2] if compliance >= 85 else (colors[1] if compliance >= 70 else colors[0])

    ax.barh(["Vuln SLA"], [compliance], color=color, height=0.4)
    ax.barh(["Vuln SLA"], [100], color="#E0E0E0", height=0.4, zorder=0)
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter())
    ax.set_title(f"Vulnerability SLA Compliance: {compliance}%", fontweight="bold")
    ax.text(compliance + 1, 0, f"{compliance}%", va="center", fontweight="bold", fontsize=12)

    path = output_dir / "chart_sla_compliance.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _chart_alert_quality(report, output_dir, plt):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    tp = report.alert_quality.true_positives
    fp = report.alert_quality.false_positives
    total = report.alert_quality.total_alerts
    other = total - tp - fp

    ax1.pie([tp, fp, other], labels=["True Positives", "False Positives", "Other"],
            colors=["#28A745", "#E60000", "#B0B0B0"], autopct="%1.1f%%", startangle=90)
    ax1.set_title("Alert Quality Breakdown", fontweight="bold")

    precision = report.alert_quality.precision_pct
    fpr = report.alert_quality.false_positive_rate_pct
    ax2.bar(["Precision", "False Positive Rate"], [precision, fpr],
            color=["#28A745", "#E60000"])
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("%")
    ax2.set_title("Alert Metrics", fontweight="bold")
    for i, v in enumerate([precision, fpr]):
        ax2.text(i, v + 1, f"{v}%", ha="center", fontweight="bold")

    fig.tight_layout()
    path = output_dir / "chart_alert_quality.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _chart_mttd_mttr(report, output_dir, plt):
    fig, ax = plt.subplots(figsize=(7, 4))

    labels = ["MTTD", "MTTR (Respond)", "MTTR (Resolve)"]
    values = [report.mttd_mttr.mttd_hours, report.mttd_mttr.mttr_hours,
              report.mttd_mttr.mtt_resolve_hours]
    colors = ["#2196F3", "#FF9800", "#4CAF50"]

    bars = ax.bar(labels, values, color=colors)
    ax.set_ylabel("Hours")
    ax.set_title(f"Incident Response Metrics ({report.mttd_mttr.total_incidents} incidents)",
                 fontweight="bold")
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val}h", ha="center", fontweight="bold")

    fig.tight_layout()
    path = output_dir / "chart_mttd_mttr.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _chart_trends(report, output_dir, plt):
    fig, axes = plt.subplots(len(report.trends), 1, figsize=(10, 3 * len(report.trends)))
    if len(report.trends) == 1:
        axes = [axes]

    for ax, (name, points) in zip(axes, report.trends.items()):
        dates = [p.date for p in points]
        values = [p.value for p in points]
        ax.plot(dates, values, marker="o", linewidth=2, color="#E60000")
        ax.fill_between(range(len(dates)), values, alpha=0.1, color="#E60000")
        ax.set_title(name, fontweight="bold")
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=45, ha="right", fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    path = output_dir / "chart_trends.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
