"""Orchestration: scan files/directories and produce classification reports."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import ClassificationReport, FileScanResult, Severity, DataCategory
from .classifier import scan_file, scan_directory


def scan(
    path: Path,
    extensions: Optional[list[str]] = None,
) -> ClassificationReport:
    """Scan a file or directory and produce a classification report."""
    all_results: list[FileScanResult] = []

    if path.is_file():
        matches = scan_file(path)
        all_results.append(FileScanResult(
            file_path=str(path),
            file_size_bytes=path.stat().st_size,
            matches=matches,
        ))
    elif path.is_dir():
        file_matches: dict[str, list] = {}
        for match in scan_directory(path, extensions):
            file_matches.setdefault(match.file_path, []).append(match)
        for fp, matches in file_matches.items():
            fpath = Path(fp)
            try:
                size = fpath.stat().st_size
            except OSError:
                size = 0
            all_results.append(FileScanResult(
                file_path=fp,
                file_size_bytes=size,
                matches=matches,
            ))
    else:
        # path doesn't exist — still produce a valid report
        pass

    total_matches = sum(r.match_count for r in all_results)
    files_with_findings = sum(1 for r in all_results if r.match_count > 0)
    critical = sum(1 for r in all_results for m in r.matches if m.severity == Severity.CRITICAL)
    high = sum(1 for r in all_results for m in r.matches if m.severity == Severity.HIGH)
    medium = sum(1 for r in all_results for m in r.matches if m.severity == Severity.MEDIUM)
    low = sum(1 for r in all_results for m in r.matches if m.severity == Severity.LOW)

    by_category: dict[str, int] = {}
    for r in all_results:
        for m in r.matches:
            cat = m.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

    return ClassificationReport(
        report_id=str(uuid.uuid4()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        scan_root=str(path),
        total_files_scanned=len(all_results),
        total_matches=total_matches,
        files_with_findings=files_with_findings,
        critical_findings=critical,
        high_findings=high,
        medium_findings=medium,
        low_findings=low,
        by_category=by_category,
        results=all_results,
    )
