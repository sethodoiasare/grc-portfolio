"""Generate posture reports: JSON export + PDF summary."""

import json
from pathlib import Path
from typing import Optional

from .models import PostureReport, CheckStatus, Severity
from .checks.registry import CIS_TO_VODAFONE


def export_json(report: PostureReport, output_path: Path) -> Path:
    """Export the posture report as structured JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = report.to_dict()
    output_path.write_text(json.dumps(data, indent=2, default=str))
    return output_path


# ── PDF helpers ────────────────────────────────────────────────

def _p(text, style):
    """Wrap text in a ReportLab Paragraph so it word-wraps inside table cells."""
    from reportlab.platypus import Paragraph
    return Paragraph(str(text), style)


def _hdr_row(labels, style):
    """Build a header row of bold Paragraph cells."""
    return [_p(l, style) for l in labels]


def export_pdf(report: PostureReport, output_path: Path) -> Path:
    """Generate a professional PDF posture report using ReportLab.

    All table cells use Paragraph objects so text wraps correctly within
    column boundaries. Follows P1 report_generator.py conventions.
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
        raise ImportError("reportlab required for PDF output. Install with: pip install reportlab")

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

    VODAFONE_RED = HexColor("#E60000")
    GREEN_BG = HexColor("#D4EDDA")
    AMBER_BG = HexColor("#FFF3CD")
    RED_BG = HexColor("#F8D7DA")
    HEADER_BG = HexColor("#E60000")
    LABEL_BG = HexColor("#F5F5F5")
    ROW_A = HexColor("#FFFFFF")
    ROW_B = HexColor("#FAFAFA")
    BORDER = HexColor("#CCCCCC")

    story = []

    # ── Cover ──────────────────────────────────────────────────
    story.append(Paragraph(
        "Cloud Posture Snapshot",
        ParagraphStyle("Title", parent=styles["Title"], fontSize=20, leading=24,
                       textColor=VODAFONE_RED, spaceAfter=4),
    ))
    story.append(Paragraph(
        f"Vodafone GRC — CIS Benchmark Assessment<br/>"
        f"Standard: CYBER_038 — Secure System Management & Protection",
        ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=9,
                       textColor=HexColor("#666666"), spaceAfter=10),
    ))
    story.append(HRFlowable(width="100%", color=VODAFONE_RED, thickness=1.5))
    story.append(Spacer(1, 0.5 * cm))

    # ── Metadata ───────────────────────────────────────────────
    rag = report.rag_status()
    rag_colour = {"GREEN": GREEN_BG, "AMBER": AMBER_BG, "RED": RED_BG}[rag]
    meta = [
        [_p("Provider", cell_bold), _p(report.provider, cell_body)],
        [_p("Account ID", cell_bold), _p(report.account_id, cell_body)],
        [_p("CIS Benchmark", cell_bold), _p(report.cis_benchmark_version, cell_body)],
        [_p("Generated", cell_bold), _p(report.generated_at[:19].replace("T", " "), cell_body)],
        [_p("Report ID", cell_bold), _p(report.report_id, cell_sm)],
        [_p("RAG Status", cell_bold), _p(rag, cell_bold)],
    ]
    meta_table = Table(meta, colWidths=[4 * cm, 14 * cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LABEL_BG),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND", (1, -1), (1, -1), rag_colour),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.7 * cm))

    # ── Summary ────────────────────────────────────────────────
    story.append(Paragraph("Assessment Summary", ParagraphStyle(
        "H2", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=HexColor("#333333"),
    )))
    s = report.summary
    summary_data = [
        _hdr_row(["Total", "Passed", "Failed", "N/A", "Pass Rate", "Critical", "High"], cell_hdr),
        [_p(str(s.total_checks), cell_bold), _p(str(s.passed), cell_bold),
         _p(str(s.failed), cell_bold), _p(str(s.not_applicable), cell_bold),
         _p(f"{s.pass_rate_pct}%", cell_bold), _p(str(s.critical_failures), cell_bold),
         _p(str(s.high_failures), cell_bold)],
    ]
    summary_table = Table(summary_data, colWidths=[2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 3 * cm, 2.5 * cm, 2.5 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.6 * cm))

    # ── Management Summary ─────────────────────────────────────
    story.append(Paragraph("Management Summary", ParagraphStyle(
        "H2b", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=HexColor("#333333"),
    )))
    story.append(Paragraph(report.management_summary, body_text))
    story.append(Spacer(1, 0.6 * cm))

    # ── Vodafone Controls ──────────────────────────────────────
    story.append(Paragraph("Vodafone Control Coverage", ParagraphStyle(
        "H2c", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=HexColor("#333333"),
    )))
    control_sections = sorted({
        f.cis_section for f in report.findings
        if f.cis_section and f.status != CheckStatus.NA
    })
    control_rows = [_hdr_row(["CIS Section", "Vodafone Control", "D Statement"], cell_hdr)]
    for section in control_sections:
        name, d_stmt = CIS_TO_VODAFONE.get(section, ("General security control", "D1"))
        control_rows.append([
            _p(f"Section {section}.x", cell_body),
            _p(name, cell_body),
            _p(d_stmt, cell_body),
        ])
    ctrl_table = Table(control_rows, colWidths=[3.5 * cm, 11.5 * cm, 3 * cm])
    ctrl_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
    ]))
    story.append(ctrl_table)
    story.append(Spacer(1, 0.6 * cm))

    # ── Findings table — 4 readable columns ─────────────────────
    story.append(Paragraph("Findings Detail", ParagraphStyle(
        "H2d", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=HexColor("#333333"),
    )))

    active = [f for f in report.findings if f.status != CheckStatus.NA]
    f_rows = [_hdr_row(["ID", "Check Title & Finding", "Status", "Sev"], cell_hdr)]
    for f in active:
        detail = f"<b>{f.check_title}</b><br/>" \
                 f"<font color='#555555'>{f.finding}</font><br/>" \
                 f"<font color='#888888' size='7'><i>Resource: {f.resource}</i></font>"
        f_rows.append([
            _p(f.check_id, cell_bold),
            _p(detail, cell_sm),
            _p(f.status.value, cell_bold),
            _p(f.severity.value, cell_bold),
        ])

    f_table = Table(f_rows, colWidths=[1.5 * cm, 11.5 * cm, 2.5 * cm, 2.5 * cm])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (3, -1), "CENTER"),
    ]
    for i, f in enumerate(active, 1):
        if f.status == CheckStatus.PASS:
            style_cmds.append(("BACKGROUND", (2, i), (2, i), GREEN_BG))
        elif f.status == CheckStatus.FAIL:
            style_cmds.append(("BACKGROUND", (2, i), (2, i), RED_BG))
    f_table.setStyle(TableStyle(style_cmds))
    story.append(f_table)
    story.append(Spacer(1, 0.6 * cm))

    # ── Critical failures ──────────────────────────────────────
    if report.critical_failures:
        story.append(PageBreak())
        story.append(Paragraph("Critical & High-Severity Failures", ParagraphStyle(
            "H2e", parent=styles["Heading2"], fontSize=13, leading=16,
            spaceBefore=12, spaceAfter=8, textColor=HexColor("#E60000"),
        )))

        cf_rows = [_hdr_row(["Sev", "ID", "Title", "Finding", "Remediation"], cell_hdr)]
        for cf in report.critical_failures:
            sev = cf.get("severity", "HIGH")
            sev_bg = RED_BG if sev == "CRITICAL" else AMBER_BG
            cf_rows.append([
                _p(sev, cell_bold),
                _p(cf.get("check_id", ""), cell_bold),
                _p(cf.get("check_title", ""), cell_body),
                _p(cf.get("finding", ""), cell_sm),
                _p(cf.get("remediation", ""), cell_sm),
            ])
            # Colour the severity cell
            ri = len(cf_rows) - 1

        cf_table = Table(cf_rows, colWidths=[2 * cm, 1.5 * cm, 4 * cm, 5 * cm, 5.5 * cm])
        cf_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
        ]
        # Colour severity column and row
        for i, cf in enumerate(report.critical_failures, 1):
            sev = cf.get("severity", "HIGH")
            sev_bg = RED_BG if sev == "CRITICAL" else AMBER_BG
            cf_style.append(("BACKGROUND", (0, i), (0, i), sev_bg))
        cf_table.setStyle(TableStyle(cf_style))
        story.append(cf_table)

    # ── Footer ─────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", color=HexColor("#CCCCCC"), thickness=0.5))
    story.append(Paragraph(
        f"Cloud Posture Snapshot — Vodafone GRC Portfolio | "
        f"Generated {report.generated_at[:19].replace('T', ' ')} UTC | "
        f"Report ID: {report.report_id[:8]}",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7,
                       textColor=HexColor("#999999"), leading=9),
    ))

    doc.build(story)
    return output_path
