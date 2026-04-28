"""Export classification reports as JSON."""

import json
from pathlib import Path

from .models import ClassificationReport


def export_json(report: ClassificationReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, default=str))
    return output_path
