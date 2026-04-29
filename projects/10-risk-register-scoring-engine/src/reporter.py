"""Report generation: ASCII matrix, summaries, JSON/CSV/PDF export."""

import csv
import json
from io import StringIO
from pathlib import Path
from datetime import date, datetime
from collections import Counter

from .models import Risk, RiskRegister, RiskLevel
from .register import get_risk_matrix
from .cvss_calc import get_severity
from .ssvc_calc import ssvc_to_action


# Risk level colour markers (no emoji, ANSI-friendly)
_LEVEL_MARKER = {
    "CRITICAL": "!!",
    "HIGH": "! ",
    "MEDIUM": "~ ",
    "LOW": ". ",
}


def print_risk_matrix(register: RiskRegister) -> str:
    """Generate an ASCII 5x5 risk matrix heatmap.

    Returns the formatted string (also prints it).
    """
    matrix = get_risk_matrix(register)
    cells = matrix["cells"]

    # Labels for matrix zones
    zone_labels = {
        (0, 0): "LOW", (0, 1): "LOW", (1, 0): "LOW", (1, 1): "LOW",
        (0, 2): "MED", (1, 2): "MED", (2, 0): "MED", (2, 1): "MED",
        (0, 3): "MED", (1, 3): "HIGH", (2, 2): "MED", (3, 0): "MED",
        (3, 1): "MED", (2, 3): "HIGH", (3, 2): "HIGH", (0, 4): "HIGH",
        (1, 4): "HIGH", (4, 0): "MED", (4, 1): "MED", (2, 4): "CRIT",
        (3, 3): "HIGH", (4, 2): "HIGH", (3, 4): "CRIT", (4, 3): "CRIT",
        (4, 4): "CRIT",
    }

    lines = []
    lines.append("")
    lines.append("  RISK MATRIX (5x5) — Likelihood vs Impact")
    lines.append("  " + "=" * 55)
    lines.append("")
    lines.append("  IMPACT ->    1       2       3       4       5")
    lines.append("  LIKELIHOOD   VeryLow  Low    Medium  High   VeryHigh")
    lines.append("  " + "-" * 55)

    for li in range(4, -1, -1):  # Top-down: high likelihood first
        row_cells = []
        for im in range(5):
            count = cells[li][im]
            zone = zone_labels.get((li, im), "MED")
            if count > 0:
                row_cells.append(f"[{zone:>4}:{count:>2}]")
            else:
                row_cells.append(f"[  .  ]")
        label = f"L{li + 1}"
        lines.append(f"  {label}  " + "  ".join(row_cells))

    lines.append("  " + "-" * 55)
    lines.append("")

    total = sum(sum(row) for row in cells)
    lines.append(f"  Total risks: {total}")
    lines.append("")

    output = "\n".join(lines)
    print(output)
    return output


def print_risk_summary(register: RiskRegister) -> str:
    """Print a summary of the risk register by level, category, and status.

    Returns the formatted string (also prints it).
    """
    lines = []
    lines.append("")
    lines.append("  RISK REGISTER SUMMARY")
    lines.append("  " + "=" * 55)
    lines.append("")

    # By risk level
    level_counts = Counter(r.risk_level.value for r in register.risks)
    lines.append("  By Risk Level:")
    for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = level_counts.get(level, 0)
        marker = _LEVEL_MARKER.get(level, "  ")
        bar = "#" * min(count, 40)
        lines.append(f"    {marker} {level:<10}: {count:>3}  {bar}")
    lines.append(f"    {'─' * 45}")
    lines.append(f"    {'TOTAL':<12}: {len(register.risks):>3}")
    lines.append("")

    # By category
    cat_counts = Counter(r.category.value for r in register.risks)
    lines.append("  By Category:")
    for cat, count in sorted(cat_counts.items()):
        lines.append(f"    {cat:<20}: {count:>3}")
    lines.append("")

    # By status
    status_counts = Counter(r.status.value for r in register.risks)
    lines.append("  By Status:")
    for status, count in sorted(status_counts.items()):
        lines.append(f"    {status:<20}: {count:>3}")
    lines.append("")

    # Top risks
    lines.append("  Top Risks by CVSS Score:")
    sorted_risks = sorted(register.risks, key=lambda r: r.cvss_score, reverse=True)
    for r in sorted_risks[:5]:
        marker = _LEVEL_MARKER.get(r.risk_level.value, "  ")
        lines.append(
            f"    {marker} {r.risk_id}  CVSS {r.cvss_score:<4}  "
            f"SSVC {r.ssvc_decision.value:<10}  {r.title[:50]}"
        )
    lines.append("")

    output = "\n".join(lines)
    print(output)
    return output


def print_risk_detail(risk: Risk) -> str:
    """Print a single risk in card format.

    Returns the formatted string (also prints it).
    """
    marker = _LEVEL_MARKER.get(risk.risk_level.value, "  ")
    sev = get_severity(risk.cvss_score)
    action = ssvc_to_action(risk.ssvc_decision)

    lines = []
    lines.append("")
    lines.append(f"  {'=' * 60}")
    lines.append(f"  {marker} RISK: {risk.risk_id} — {risk.title}")
    lines.append(f"  {'=' * 60}")
    lines.append(f"  Status:       {risk.status.value}")
    lines.append(f"  Category:     {risk.category.value}")
    lines.append(f"  Owner:        {risk.owner or '(unassigned)'}")
    lines.append(f"  Identified:   {risk.identified_date}")
    lines.append(f"  Risk Level:   {risk.risk_level.value}")
    lines.append(f"  Impact:       {risk.impact_score}/100")
    lines.append(f"  Likelihood:   {risk.likelihood_score}/100")
    lines.append(f"  CVSS Score:   {risk.cvss_score} ({sev})")
    lines.append(f"  CVSS Vector:  {risk.cvss_vector}")
    lines.append(f"  SSVC Decision:{risk.ssvc_decision.value}")
    lines.append(f"  SSVC Action:  {action[:80]}...")
    if risk.acceptance_rationale:
        lines.append(f"  Acceptance:   {risk.acceptance_rationale[:100]}")
    if risk.treatment_plan:
        lines.append(f"  Treatment:    {risk.treatment_plan[:100]}")
    if risk.review_date:
        overdue = " [OVERDUE]" if risk.review_date < date.today() else ""
        lines.append(f"  Review Date:  {risk.review_date}{overdue}")
    if risk.control_mapping:
        lines.append(f"  Controls:     {', '.join(risk.control_mapping)}")
    lines.append(f"  Description:  {risk.description[:200]}")
    lines.append(f"  {'=' * 60}")
    lines.append("")

    output = "\n".join(lines)
    print(output)
    return output


def save_register_json(register: RiskRegister, path: Path) -> Path:
    """Export the full risk register as JSON.

    Args:
        register: The RiskRegister to export.
        path: Output file path.

    Returns:
        The path written.
    """
    data = {
        "metadata": {
            "created": register.created,
            "updated": register.updated,
            "owner": register.owner,
            "total_risks": len(register.risks),
        },
        "risks": [],
    }
    for risk in register.risks:
        risk_dict = {
            "risk_id": risk.risk_id,
            "title": risk.title,
            "description": risk.description,
            "category": risk.category.value,
            "owner": risk.owner,
            "identified_date": risk.identified_date.isoformat(),
            "status": risk.status.value,
            "cvss_score": risk.cvss_score,
            "cvss_vector": risk.cvss_vector,
            "ssvc_decision": risk.ssvc_decision.value,
            "impact_score": risk.impact_score,
            "likelihood_score": risk.likelihood_score,
            "risk_level": risk.risk_level.value,
            "acceptance_rationale": risk.acceptance_rationale,
            "treatment_plan": risk.treatment_plan,
            "review_date": risk.review_date.isoformat() if risk.review_date else None,
            "control_mapping": risk.control_mapping,
        }
        data["risks"].append(risk_dict)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    return path


def save_register_csv(register: RiskRegister, path: Path) -> Path:
    """Export the full risk register as CSV.

    Args:
        register: The RiskRegister to export.
        path: Output file path.

    Returns:
        The path written.
    """
    fieldnames = [
        "risk_id", "title", "description", "category", "owner",
        "identified_date", "status", "cvss_score", "cvss_vector",
        "ssvc_decision", "impact_score", "likelihood_score", "risk_level",
        "acceptance_rationale", "treatment_plan", "review_date", "control_mapping",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for risk in register.risks:
            row = {
                "risk_id": risk.risk_id,
                "title": risk.title,
                "description": risk.description,
                "category": risk.category.value,
                "owner": risk.owner,
                "identified_date": risk.identified_date.isoformat(),
                "status": risk.status.value,
                "cvss_score": risk.cvss_score,
                "cvss_vector": risk.cvss_vector,
                "ssvc_decision": risk.ssvc_decision.value,
                "impact_score": risk.impact_score,
                "likelihood_score": risk.likelihood_score,
                "risk_level": risk.risk_level.value,
                "acceptance_rationale": risk.acceptance_rationale or "",
                "treatment_plan": risk.treatment_plan or "",
                "review_date": risk.review_date.isoformat() if risk.review_date else "",
                "control_mapping": ";".join(risk.control_mapping),
            }
            writer.writerow(row)
    return path


# ── PDF helpers ────────────────────────────────────────────────


def _p(text, style):
    """Wrap text in a ReportLab Paragraph so it word-wraps inside table cells."""
    from reportlab.platypus import Paragraph
    return Paragraph(str(text), style)


def _hdr_row(labels, style):
    """Build a header row of bold Paragraph cells."""
    return [_p(l, style) for l in labels]


# ── PDF export ─────────────────────────────────────────────────


def export_pdf(register: RiskRegister, output_path: str) -> str:
    """Generate a professional PDF risk register report using ReportLab.

    All table cells use Paragraph objects so text wraps correctly within
    column boundaries. Follows P5 reporter.py conventions.

    Sections: cover page, executive summary (by level/category/status),
    5x5 risk matrix, top 5 by CVSS, overdue reviews, full register.

    Args:
        register: The RiskRegister to export.
        output_path: Output file path (str or Path).

    Returns:
        The path written as a string.
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

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()

    # Shared cell styles — wordWrap is the key for table cell wrapping
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

    # Brand colours (exact P5 pattern)
    VODAFONE_RED = HexColor("#E60000")
    RAG_GREEN_BG = HexColor("#D4EDDA")
    RAG_AMBER_BG = HexColor("#FFF3CD")
    RAG_RED_BG = HexColor("#F8D7DA")
    CRITICAL_BG = HexColor("#F5C6CB")
    HEADER_BG = HexColor("#E60000")
    LABEL_BG = HexColor("#F5F5F5")
    ROW_A = HexColor("#FFFFFF")
    ROW_B = HexColor("#FAFAFA")
    BORDER = HexColor("#CCCCCC")

    def _level_bg(level_name: str):
        """Return background colour for a risk level."""
        return {
            "CRITICAL": CRITICAL_BG,
            "HIGH": RAG_RED_BG,
            "MEDIUM": RAG_AMBER_BG,
            "LOW": RAG_GREEN_BG,
        }.get(level_name, ROW_A)

    # Page footer callback
    def _on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor("#999999"))
        footer_text = "Risk Register + Scoring Engine — GRC Portfolio | CONFIDENTIAL"
        canvas.drawString(
            doc.leftMargin, doc.bottomMargin - 0.5 * cm, footer_text
        )
        canvas.drawRightString(
            doc.width + doc.leftMargin,
            doc.bottomMargin - 0.5 * cm,
            f"Page {canvas.getPageNumber()}",
        )
        canvas.restoreState()

    story = []

    # ── Cover ──────────────────────────────────────────────────
    story.append(Paragraph(
        "Risk Register Report",
        ParagraphStyle("RiskTitle", parent=styles["Title"], fontSize=20, leading=24,
                       textColor=VODAFONE_RED, spaceAfter=4),
    ))
    story.append(Paragraph(
        "CVSS v3.1 / SSVC v2 — Full Assessment Report",
        ParagraphStyle("RiskSubtitle", parent=styles["Normal"], fontSize=9,
                       textColor=HexColor("#666666"), spaceAfter=10),
    ))
    story.append(HRFlowable(width="100%", color=VODAFONE_RED, thickness=1.5))
    story.append(Spacer(1, 0.5 * cm))

    # Metadata table
    created_disp = register.created[:19].replace("T", " ") if register.created else "N/A"
    updated_disp = register.updated[:19].replace("T", " ") if register.updated else "N/A"

    meta = [
        [_p("Owner", cell_bold), _p(register.owner or "(unassigned)", cell_body)],
        [_p("Created", cell_bold), _p(created_disp, cell_body)],
        [_p("Updated", cell_bold), _p(updated_disp, cell_body)],
        [_p("Total Risks", cell_bold), _p(str(len(register.risks)), cell_bold)],
    ]
    meta_table = Table(meta, colWidths=[4 * cm, 14 * cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LABEL_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.7 * cm))

    # ── Executive Summary ──────────────────────────────────────
    story.append(Paragraph("Executive Summary", ParagraphStyle(
        "RiskH2", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=HexColor("#333333"),
    )))

    # Counts
    level_counts = Counter(r.risk_level.value for r in register.risks)
    cat_counts = Counter(r.category.value for r in register.risks)
    status_counts = Counter(r.status.value for r in register.risks)

    # Risks by Level table
    story.append(Paragraph("Risks by Level", ParagraphStyle(
        "RiskH3a", parent=styles["Heading3"], fontSize=10, leading=13,
        spaceBefore=8, spaceAfter=4, textColor=HexColor("#333333"),
    )))
    lvl_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    level_data = [_hdr_row(["Level", "Count"], cell_hdr)]
    for level in lvl_levels:
        level_data.append([
            _p(level, cell_bold),
            _p(str(level_counts.get(level, 0)), cell_bold),
        ])
    level_table = Table(level_data, colWidths=[9 * cm, 9 * cm])
    level_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ]
    for i, level in enumerate(lvl_levels, 1):
        level_style.append(("BACKGROUND", (0, i), (-1, i), _level_bg(level)))
    level_table.setStyle(TableStyle(level_style))
    story.append(level_table)
    story.append(Spacer(1, 0.4 * cm))

    # Risks by Category table
    story.append(Paragraph("Risks by Category", ParagraphStyle(
        "RiskH3b", parent=styles["Heading3"], fontSize=10, leading=13,
        spaceBefore=8, spaceAfter=4, textColor=HexColor("#333333"),
    )))
    lvl_cats = ["INFRASTRUCTURE", "APPLICATION", "DATA", "VENDOR", "HUMAN", "COMPLIANCE"]
    cat_data = [_hdr_row(["Category", "Count"], cell_hdr)]
    for cat in lvl_cats:
        cat_data.append([
            _p(cat, cell_bold),
            _p(str(cat_counts.get(cat, 0)), cell_bold),
        ])
    cat_table = Table(cat_data, colWidths=[9 * cm, 9 * cm])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 0.4 * cm))

    # Risks by Status table
    story.append(Paragraph("Risks by Status", ParagraphStyle(
        "RiskH3c", parent=styles["Heading3"], fontSize=10, leading=13,
        spaceBefore=8, spaceAfter=4, textColor=HexColor("#333333"),
    )))
    lvl_statuses = ["IDENTIFIED", "ANALYZING", "ACCEPTED", "MITIGATED", "CLOSED"]
    status_data = [_hdr_row(["Status", "Count"], cell_hdr)]
    for status in lvl_statuses:
        status_data.append([
            _p(status, cell_bold),
            _p(str(status_counts.get(status, 0)), cell_bold),
        ])
    status_table = Table(status_data, colWidths=[9 * cm, 9 * cm])
    status_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
    ]))
    story.append(status_table)

    # ── 5x5 Risk Matrix ────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5x5 Risk Matrix", ParagraphStyle(
        "RiskH2b", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=HexColor("#333333"),
    )))
    story.append(Paragraph(
        "Likelihood (rows) vs Impact (columns). "
        "Colour intensity reflects risk zone severity.",
        body_text,
    ))
    story.append(Spacer(1, 0.3 * cm))

    matrix = get_risk_matrix(register)
    cells = matrix["cells"]

    impact_labels = ["1\nVeryLow", "2\nLow", "3\nMedium", "4\nHigh", "5\nVeryHigh"]
    likelihood_labels = ["1\nVeryLow", "2\nLow", "3\nMedium", "4\nHigh", "5\nVeryHigh"]

    def _cell_zone_color(li: int, im: int):
        """Return background colour for a matrix cell by risk zone."""
        product = (li + 1) * (im + 1)
        if product <= 4:
            return RAG_GREEN_BG
        elif product <= 9:
            return RAG_AMBER_BG
        elif product <= 19:
            return RAG_RED_BG
        else:
            return CRITICAL_BG

    # 6x6 grid: header row + header column + 5x5 data cells
    matrix_data = [[_p("L / I", cell_hdr)] + [_p(l, cell_hdr) for l in impact_labels]]
    for li in range(4, -1, -1):  # top-down: high likelihood first
        row = [_p(likelihood_labels[li], cell_hdr)]
        for im in range(5):
            count = cells[li][im]
            display = str(count) if count > 0 else "-"
            row.append(_p(display, cell_bold))
        matrix_data.append(row)

    matrix_table = Table(matrix_data, colWidths=[2.5 * cm] + [2.4 * cm] * 5)
    matrix_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BACKGROUND", (0, 1), (0, -1), HEADER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ]
    # Colour data cells by zone
    row_labels = [4, 3, 2, 1, 0]  # rows in display order
    for ri, li in enumerate(row_labels, 1):
        for im in range(5):
            matrix_style.append(
                ("BACKGROUND", (im + 1, ri), (im + 1, ri), _cell_zone_color(li, im))
            )
    matrix_table.setStyle(TableStyle(matrix_style))
    story.append(matrix_table)
    story.append(Spacer(1, 0.4 * cm))

    # Legend
    legend_data = [[
        _p("", cell_body),
        _p("GREEN = LOW", cell_body),
        _p("AMBER = MEDIUM", cell_body),
        _p("RED = HIGH", cell_body),
        _p("DARK RED = CRITICAL", cell_body),
    ]]
    legend_table = Table(legend_data, colWidths=[1 * cm, 3.5 * cm, 4 * cm, 3.5 * cm, 5 * cm])
    legend_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), RAG_GREEN_BG),
        ("BACKGROUND", (1, 0), (1, 0), RAG_GREEN_BG),
        ("BACKGROUND", (2, 0), (2, 0), RAG_AMBER_BG),
        ("BACKGROUND", (3, 0), (3, 0), RAG_RED_BG),
        ("BACKGROUND", (4, 0), (4, 0), CRITICAL_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(legend_table)

    # ── Top 5 Risks by CVSS ────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Top 5 Risks by CVSS Score", ParagraphStyle(
        "RiskH2c", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=HexColor("#333333"),
    )))

    sorted_risks = sorted(register.risks, key=lambda r: r.cvss_score, reverse=True)[:5]
    top_data = [
        _hdr_row(["Risk ID", "Title", "CVSS Score", "CVSS Vector", "SSVC Decision", "Level"], cell_hdr)
    ]
    for r in sorted_risks:
        top_data.append([
            _p(r.risk_id, cell_bold),
            _p(r.title, cell_body),
            _p(f"{r.cvss_score:.1f}", cell_bold),
            _p(r.cvss_vector, cell_sm),
            _p(r.ssvc_decision.value, cell_body),
            _p(r.risk_level.value, cell_bold),
        ])
    top_table = Table(
        top_data,
        colWidths=[2.5 * cm, 5.5 * cm, 2 * cm, 4.5 * cm, 2 * cm, 2 * cm],
    )
    top_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
    ]
    for i, r in enumerate(sorted_risks, 1):
        top_style.append(("BACKGROUND", (5, i), (5, i), _level_bg(r.risk_level.value)))
        if r.risk_level.value == "CRITICAL":
            top_style.append(("BACKGROUND", (0, i), (-1, i), CRITICAL_BG))
    top_table.setStyle(TableStyle(top_style))
    story.append(top_table)
    story.append(Spacer(1, 0.6 * cm))

    # ── Overdue Reviews ────────────────────────────────────────
    from .register import get_overdue_reviews
    overdue = get_overdue_reviews(register)
    if overdue:
        story.append(Paragraph("Overdue Reviews", ParagraphStyle(
            "RiskH2d", parent=styles["Heading2"], fontSize=13, leading=16,
            spaceBefore=12, spaceAfter=8, textColor=VODAFONE_RED,
        )))

        today = date.today()
        overdue_data = [
            _hdr_row(["Risk ID", "Title", "Level", "Review Date", "Days Overdue"], cell_hdr)
        ]
        for r in overdue:
            days_overdue = (today - r.review_date).days if r.review_date else 0
            overdue_data.append([
                _p(r.risk_id, cell_bold),
                _p(r.title, cell_body),
                _p(r.risk_level.value, cell_bold),
                _p(r.review_date.isoformat() if r.review_date else "N/A", cell_body),
                _p(str(days_overdue), cell_bold),
            ])
        overdue_table = Table(
            overdue_data,
            colWidths=[2.5 * cm, 6.5 * cm, 2 * cm, 3.5 * cm, 3.5 * cm],
        )
        overdue_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ]
        for i, _r in enumerate(overdue, 1):
            overdue_style.append(("BACKGROUND", (0, i), (-1, i), RAG_RED_BG))
        overdue_table.setStyle(TableStyle(overdue_style))
        story.append(overdue_table)
        story.append(Spacer(1, 0.5 * cm))

    # ── Full Risk Register ─────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Full Risk Register", ParagraphStyle(
        "RiskH2e", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=HexColor("#333333"),
    )))

    full_data = [
        _hdr_row(["Risk ID", "Title", "Category", "CVSS", "SSVC", "Level", "Status"], cell_hdr)
    ]
    for r in register.risks:
        full_data.append([
            _p(r.risk_id, cell_bold),
            _p(r.title, cell_body),
            _p(r.category.value, cell_sm),
            _p(f"{r.cvss_score:.1f}", cell_body),
            _p(r.ssvc_decision.value, cell_sm),
            _p(r.risk_level.value, cell_bold),
            _p(r.status.value, cell_sm),
        ])

    full_table = Table(
        full_data,
        colWidths=[2 * cm, 5 * cm, 2.5 * cm, 1.5 * cm, 2 * cm, 2 * cm, 3 * cm],
    )
    full_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
    ]
    for i, r in enumerate(register.risks, 1):
        full_style.append(("BACKGROUND", (5, i), (5, i), _level_bg(r.risk_level.value)))
    full_table.setStyle(TableStyle(full_style))
    story.append(full_table)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return str(output_path)
