"""Output generators — terminal summary, JSON, CSV, and PDF reports."""

import json
import csv
from datetime import datetime
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


# ── PDF helpers ────────────────────────────────────────────────

def _p(text, style):
    """Wrap text in a ReportLab Paragraph so it word-wraps inside table cells."""
    from reportlab.platypus import Paragraph
    return Paragraph(str(text), style)


def _hdr_row(labels, style):
    """Build a header row of bold Paragraph cells."""
    return [_p(l, style) for l in labels]


def export_pdf(results: list[CoverageResult], output_path: str) -> Path:
    """Generate a professional PDF coverage report using ReportLab.

    All table cells use Paragraph objects so text wraps correctly within
    column boundaries. Follows P5 reporter.py conventions.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.colors import HexColor
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, HRFlowable,
        )
    except ImportError:
        raise ImportError(
            "reportlab required for PDF output. Install with: pip install reportlab"
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()

    # ── Shared cell styles ──────────────────────────────────────
    cell_body = ParagraphStyle(
        "CellBody", parent=styles["Normal"],
        fontSize=7.5, leading=10, wordWrap="CJK",
    )
    cell_bold = ParagraphStyle(
        "CellBold", parent=cell_body,
        fontName="Helvetica-Bold",
    )
    cell_hdr = ParagraphStyle(
        "CellHdr", parent=cell_body,
        fontName="Helvetica-Bold", fontSize=7.5, leading=10,
        textColor=HexColor("#FFFFFF"),
    )
    cell_sm = ParagraphStyle(
        "CellSm", parent=cell_body,
        fontSize=7, leading=9, wordWrap="CJK",
    )
    body_text = ParagraphStyle(
        "BodyText", parent=styles["Normal"],
        fontSize=9, leading=13,
    )

    VODAFONE_RED = HexColor("#E60000")
    RAG_GREEN_BG = HexColor("#D4EDDA")
    RAG_AMBER_BG = HexColor("#FFF3CD")
    RAG_RED_BG = HexColor("#F8D7DA")
    HEADER_BG = VODAFONE_RED
    LABEL_BG = HexColor("#F5F5F5")
    ROW_A = HexColor("#FFFFFF")
    ROW_B = HexColor("#FAFAFA")
    BORDER = HexColor("#CCCCCC")

    # ── Custom heading styles ────────────────────────────────────
    CovTitle = ParagraphStyle(
        "CovTitle", parent=styles["Title"],
        fontSize=20, leading=24, textColor=VODAFONE_RED, spaceAfter=4,
    )
    CovH2 = ParagraphStyle(
        "CovH2", parent=styles["Heading2"],
        fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=HexColor("#333333"),
    )
    CovFooter = ParagraphStyle(
        "CovFooter", parent=styles["Normal"],
        fontSize=7, textColor=HexColor("#999999"), leading=9,
    )

    story = []

    # ── Cover ────────────────────────────────────────────────────
    num_frameworks = len(results)
    gen_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    story.append(Paragraph("Security Control Coverage Report", CovTitle))
    story.append(Paragraph(
        f"{num_frameworks} control framework(s) analysed<br/>"
        f"Generated: {gen_date}",
        ParagraphStyle("CovSub", parent=styles["Normal"], fontSize=9,
                       textColor=HexColor("#666666"), spaceAfter=10),
    ))
    story.append(HRFlowable(width="100%", color=VODAFONE_RED, thickness=1.5))
    story.append(Spacer(1, 0.5 * cm))

    # ── Per-framework sections ───────────────────────────────────
    for idx, r in enumerate(results):
        if idx > 0:
            story.append(PageBreak())

        rag = r.rag_status()
        rag_bg = {"GREEN": RAG_GREEN_BG, "AMBER": RAG_AMBER_BG, "RED": RAG_RED_BG}[rag]

        # Framework header
        story.append(Paragraph(f"Framework: {r.framework}", CovH2))
        story.append(Spacer(1, 0.3 * cm))

        # RAG Status badge
        rag_data = [
            [_p("RAG Status", cell_bold), _p(rag, cell_bold)],
            [_p("Coverage", cell_bold), _p(f"{r.coverage_pct}%", cell_bold)],
            [_p("Effective Coverage", cell_bold), _p(f"{r.effective_coverage_pct}%", cell_bold)],
        ]
        rag_table = Table(rag_data, colWidths=[5 * cm, 13 * cm])
        rag_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LABEL_BG),
            ("BACKGROUND", (1, 0), (1, -1), rag_bg),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ]))
        story.append(rag_table)
        story.append(Spacer(1, 0.5 * cm))

        # Summary stats table
        story.append(Paragraph("Summary Statistics", CovH2))
        total = r.total_controls
        sum_data = [
            _hdr_row(["Category", "Count", "Percentage"], cell_hdr),
            [_p("Total Controls", cell_bold), _p(str(total), cell_bold), _p("100%", cell_bold)],
            [_p("Covered", cell_body), _p(str(r.covered), cell_body), _p(f"{_pct(r.covered, total)}%", cell_body)],
            [_p("Partial", cell_body), _p(str(r.partial), cell_body), _p(f"{_pct(r.partial, total)}%", cell_body)],
            [_p("Gap", cell_body), _p(str(r.gap), cell_body), _p(f"{_pct(r.gap, total)}%", cell_body)],
        ]
        sum_table = Table(sum_data, colWidths=[8 * cm, 5 * cm, 5 * cm])
        sum_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
            ("BACKGROUND", (0, 2), (0, 2), RAG_GREEN_BG),
            ("BACKGROUND", (0, 3), (0, 3), RAG_AMBER_BG),
            ("BACKGROUND", (0, 4), (0, 4), RAG_RED_BG),
        ]))
        story.append(sum_table)
        story.append(Spacer(1, 0.5 * cm))

        # Coverage by Category table
        if r.heatmap_data:
            story.append(Paragraph("Coverage by Category", CovH2))
            cat_rows = [_hdr_row(["Category", "Coverage %", "Covered", "Partial", "Gap", "Bar"], cell_hdr)]
            for cat, data in sorted(r.heatmap_data.items()):
                pct = data["coverage_pct"]
                bar_cell = _bar_cell(pct)
                cat_rows.append([
                    _p(cat, cell_body),
                    _p(f"{pct}%", cell_bold),
                    _p(str(data["covered"]), cell_body),
                    _p(str(data["partial"]), cell_body),
                    _p(str(data["gap"]), cell_body),
                    _p(bar_cell, cell_sm),
                ])
            cat_table = Table(cat_rows, colWidths=[6 * cm, 2.5 * cm, 2 * cm, 2 * cm, 1.5 * cm, 4 * cm])
            cat_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
            ]))
            story.append(cat_table)
            story.append(Spacer(1, 0.4 * cm))

        # Gap Controls table
        if r.gaps_list:
            story.append(Paragraph(f"Gap Controls ({len(r.gaps_list)})", CovH2))
            gap_rows = [_hdr_row(["Control ID", "Title", "Category", "Remediation"], cell_hdr)]
            for g in r.gaps_list:
                remedy = generate_remediation(g.category)
                gap_rows.append([
                    _p(g.control_id, cell_bold),
                    _p(g.title, cell_body),
                    _p(g.category, cell_body),
                    _p(remedy, cell_sm),
                ])
            gap_table = Table(gap_rows, colWidths=[2 * cm, 5 * cm, 3.5 * cm, 7.5 * cm])
            gap_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
            ]))
            story.append(gap_table)
            story.append(Spacer(1, 0.4 * cm))

    # ── Action Items section ──────────────────────────────────────
    all_gaps = []
    for r in results:
        for g in r.gaps_list:
            all_gaps.append((r.framework, g))

    if all_gaps:
        story.append(PageBreak())
        story.append(Paragraph("Action Items", CovH2))
        story.append(Spacer(1, 0.2 * cm))
        action_rows = [_hdr_row(["Framework", "Control ID", "Title", "Remediation"], cell_hdr)]
        for fw_name, g in all_gaps:
            remedy = generate_remediation(g.category)
            action_rows.append([
                _p(fw_name, cell_bold),
                _p(g.control_id, cell_bold),
                _p(g.title, cell_body),
                _p(remedy, cell_sm),
            ])
        action_table = Table(action_rows, colWidths=[2.5 * cm, 2.5 * cm, 5 * cm, 8 * cm])
        action_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
        ]))
        story.append(action_table)

    # ── Footer ───────────────────────────────────────────────────
    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor("#999999"))
        footer_text = (
            "Security Control Coverage Mapper — GRC Portfolio | CONFIDENTIAL"
        )
        canvas.drawCentredString(A4[0] / 2, 1.0 * cm, footer_text)
        canvas.drawRightString(A4[0] - 1.5 * cm, 1.0 * cm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", color=HexColor("#CCCCCC"), thickness=0.5))
    story.append(Paragraph(
        f"Security Control Coverage Mapper — GRC Portfolio | CONFIDENTIAL",
        CovFooter,
    ))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return path


def _pct(part: int, total: int) -> float:
    """Return percentage, guarding against zero division."""
    if total == 0:
        return 0.0
    return round(part / total * 100, 1)


def _bar_cell(pct: float) -> str:
    """Build a visual bar string for use inside a Paragraph cell."""
    filled = max(int(pct / 10), 0)
    empty = 10 - filled
    return "|" * filled + "-" * empty
