"""CLI for Vendor Security Questionnaire Scorer."""

import argparse
import sys
from pathlib import Path

from .models import Question, Answer, Weight
from .parser import auto_detect_and_parse
from .scorer import assess_vendor
from .reporter import print_assessment, save_report_json, save_report_md
from .demo_data import get_demo_questions


def main():
    parser = argparse.ArgumentParser(
        prog="vendor-scorer",
        description="Vendor Security Questionnaire Scorer — score vendor responses and generate risk reports",
    )
    sub = parser.add_subparsers(dest="command")

    score_p = sub.add_parser("score", help="Score a vendor questionnaire")
    score_p.add_argument("--file", type=Path, help="Path to questionnaire CSV or Excel file")
    score_p.add_argument("--output", "-o", type=Path, default=Path("data/vendor-assessment.json"),
                         help="Output path for JSON/MD report")
    score_p.add_argument("--format", "-f", choices=["json", "md", "pdf", "all"], default="json",
                         help="Output format (default: json)")
    score_p.add_argument("--demo", action="store_true", help="Run with built-in demo data")

    args = parser.parse_args()

    if args.command == "score":
        if args.demo:
            vendor_name, raw_questions = get_demo_questions()
            questions = _from_dict_list(raw_questions)
        elif args.file:
            questions = auto_detect_and_parse(str(args.file))
            vendor_name = args.file.stem.replace("_", " ").replace("-", " ").title()
        else:
            print("Error: --file or --demo required")
            sys.exit(1)

        assessment = assess_vendor(vendor_name, questions)
        print_assessment(assessment)

        base = args.output
        if args.format in ("json", "all"):
            json_path = save_report_json(assessment, str(base))
            print(f"JSON report saved to {json_path}")
        if args.format in ("md", "all"):
            md_path = base.with_suffix(".md")
            save_report_md(assessment, str(md_path))
            print(f"Markdown report saved to {md_path}")
        if args.format in ("pdf", "all"):
            from .reporter import export_pdf
            pdf_path = base.with_suffix(".pdf")
            path = export_pdf(assessment, str(pdf_path))
            print(f"PDF report saved to {path}")

    else:
        parser.print_help()


def _from_dict_list(rows: list[dict]) -> list[Question]:
    """Convert list of dicts to Question objects (for demo data)."""
    questions: list[Question] = []
    for i, row in enumerate(rows, start=1):
        questions.append(Question(
            id=f"Q-{i:03d}",
            category=row["category"],
            text=row["question"],
            weight=Weight(row["weight"]),
            answer=Answer(row["answer"]),
            notes=row.get("notes", ""),
        ))
    return questions


if __name__ == "__main__":
    main()
