"""Regex-based classification engine for PII/PCI/PHI/Secrets detection."""

import re
from pathlib import Path
from typing import Optional

from .models import (
    CLASSIFICATION_RULES, ClassificationMatch, DataCategory, Severity,
)


def scan_file(file_path: Path) -> list[ClassificationMatch]:
    """Scan a single file for data classification matches."""
    matches = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError, UnicodeDecodeError):
        return matches

    for rule in CLASSIFICATION_RULES:
        pattern = re.compile(rule["pattern"])
        for lineno, line in enumerate(content.splitlines(), 1):
            for match in pattern.finditer(line):
                matched_text = match.group(0)
                # Skip false positives for generic patterns
                if _skip_false_positive(rule["id"], matched_text, line):
                    continue
                context = line.strip()
                matches.append(ClassificationMatch(
                    rule_id=rule["id"],
                    rule_title=rule["title"],
                    category=rule["category"],
                    severity=rule["severity"],
                    match_text=matched_text,
                    file_path=str(file_path),
                    line_number=lineno,
                    context=context[:200],
                ))
    return matches


def scan_directory(root: Path, extensions: Optional[list[str]] = None) -> list[ClassificationMatch]:
    """Recursively scan a directory for data classification matches."""
    all_matches = []
    root = Path(root)

    for item in root.rglob("*"):
        if not item.is_file():
            continue
        if item.name.startswith("."):
            continue
        if _is_binary(item):
            continue
        if extensions and item.suffix not in extensions:
            continue
        all_matches.extend(scan_file(item))

    return all_matches


def _skip_false_positive(rule_id: str, matched_text: str, line: str) -> bool:
    """Filter out obvious false positives for generic patterns."""
    # NHS number — require context
    if rule_id == "PHI-001":
        nhs_keywords = ["nhs", "patient", "hospital", "gp", "prescription", "health"]
        if not any(k in line.lower() for k in nhs_keywords):
            return True
    # UK passport number — 9 digits is very generic
    if rule_id == "PII-005":
        pport_keywords = ["passport", "travel document"]
        if not any(k in line.lower() for k in pport_keywords):
            return True
    # Generic API key pattern already has keyword context in the regex
    return False


def _is_binary(file_path: Path) -> bool:
    """Quick check if a file appears to be binary."""
    binary_extensions = {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".pdf",
        ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
        ".exe", ".dll", ".so", ".dylib", ".bin",
        ".mp3", ".mp4", ".avi", ".mov", ".mkv",
        ".ttf", ".otf", ".woff", ".woff2", ".eot",
        ".pyc", ".pyo", ".class",
    }
    return file_path.suffix.lower() in binary_extensions
