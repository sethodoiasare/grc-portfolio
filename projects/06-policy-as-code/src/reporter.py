"""Export policy reports as JSON."""

import json
from pathlib import Path

from .models import PolicyReport


def export_json(report: PolicyReport, output_path: Path) -> Path:
    """Export the policy report as structured JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = report.to_dict()
    output_path.write_text(json.dumps(data, indent=2, default=str))
    return output_path
