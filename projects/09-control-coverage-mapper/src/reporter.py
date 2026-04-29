"""Output generators — terminal summary, JSON, and CSV reports."""

import json
import csv
from pathlib import Path

from .models import CoverageResult, CoverageStatus
from .mapper import generate_remediation


def print_summary(results: list[CoverageResult]) -> None:
    """Print formatted coverage summary to the terminal."""
    print(f"\n{'=' * 72}")
    print("  SECURITY CONTROL COVERAGE MAPPER — RESULTS")
    print(f"{'=' * 72}")

    for r in results:
        print(f"\n  Framework: {r.framework}")
        print(f"  {'-' * 40}")
        print(f"  Total Controls:  {r.total_controls}")
        print(f"  Covered:          {r.covered}  (Fully)")
        print(f"  Partial:          {r.partial}  (Needs enrichment)")
        print(f"  Gaps:             {r.gap}  (No coverage)")
        print(f"  Coverage:         {r.coverage_pct}%")
        print(f"  Effective Cov:    {r.effective_coverage_pct}% (partial = 0.5)")
        print(f"  RAG Status:       {r.rag_status()}")

        if r.gaps_list:
            print(f"\n  GAP CONTROLS ({len(r.gaps_list)}):")
            for g in r.gaps_list:
                remedy = generate_remediation(g.category)
                print(f"    [{g.control_id}] {g.title}")
                print(f"      Category: {g.category}")
                print(f"      Fix: {remedy[:120]}...")

        if r.heatmap_data:
            print(f"\n  COVERAGE BY CATEGORY:")
            for cat, data in sorted(r.heatmap_data.items()):
                bar = _bar(data["coverage_pct"])
                print(f"    {cat:<35} {data['coverage_pct']:>5.1f}% {bar}")

    print(f"\n{'=' * 72}\n")


def _bar(pct: float, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def save_json_report(results: list[CoverageResult], output_path: str) -> Path:
    """Save full coverage results as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [r.to_dict() for r in results]
    path.write_text(json.dumps(data, indent=2, default=str))
    return path


def save_csv_report(results: list[CoverageResult], output_path: str) -> Path:
    """Save coverage results as CSV with detailed control-level rows."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Framework", "Control ID", "Title", "Category", "Status",
                          "Similarity Score", "Matched Policy Text"])
        for r in results:
            for c in r.controls:
                writer.writerow([
                    r.framework,
                    c.control_id,
                    c.title,
                    c.category,
                    c.status.value,
                    c.similarity_score,
                    (c.matched_text or "")[:200],
                ])
    return path
