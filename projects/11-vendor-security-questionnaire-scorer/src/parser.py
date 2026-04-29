"""Questionnaire parser — CSV and Excel ingestion."""

import csv
from pathlib import Path

from .models import Question, Answer, Weight


def parse_questionnaire_csv(filepath: str) -> list[Question]:
    """Parse a CSV file with columns: category, question, weight, answer, notes.

    Returns a list of Question objects with auto-generated IDs.
    """
    path = Path(filepath)
    questions: list[Question] = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            category = row.get("category", "").strip()
            text = row.get("question", "").strip()
            weight_raw = row.get("weight", "MEDIUM").strip().upper()
            answer_raw = row.get("answer", "YES").strip().upper()
            notes = row.get("notes", "").strip()

            weight = Weight(weight_raw)
            answer = Answer(answer_raw)

            questions.append(Question(
                id=f"Q-{i:03d}",
                category=category,
                text=text,
                weight=weight,
                answer=answer,
                notes=notes,
            ))

    return questions


def parse_questionnaire_excel(filepath: str) -> list[Question]:
    """Parse an Excel (.xlsx) file with columns: category, question, weight, answer, notes."""
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl is required for Excel parsing. Install with: pip install openpyxl")

    path = Path(filepath)
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    questions: list[Question] = []

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return questions

    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
    col_map = {name: idx for idx, name in enumerate(headers)}

    for i, row in enumerate(rows[1:], start=1):
        def cell(col_name: str, default: str = "") -> str:
            idx = col_map.get(col_name)
            if idx is not None and idx < len(row) and row[idx] is not None:
                return str(row[idx]).strip()
            return default

        category = cell("category")
        text = cell("question")
        weight_raw = cell("weight", "MEDIUM").upper()
        answer_raw = cell("answer", "YES").upper()
        notes = cell("notes")

        weight = Weight(weight_raw)
        answer = Answer(answer_raw)

        questions.append(Question(
            id=f"Q-{i:03d}",
            category=category,
            text=text,
            weight=weight,
            answer=answer,
            notes=notes,
        ))

    wb.close()
    return questions


def auto_detect_and_parse(filepath: str) -> list[Question]:
    """Detect file type (.csv or .xlsx) and call the appropriate parser."""
    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return parse_questionnaire_csv(filepath)
    elif suffix in (".xlsx", ".xls"):
        return parse_questionnaire_excel(filepath)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: .csv, .xlsx")
