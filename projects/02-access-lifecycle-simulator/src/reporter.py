"""Report generation for IAM Access Lifecycle Simulator.

Produces structured violation reports and access certification packs.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .models import (
    AuditReport, Violation, Severity, SEVERITY_SLA,
)


def generate_access_certification(violations: list[Violation]) -> list[dict]:
    """Produce access certification items with REVOKE/REVIEW/CONFIRM actions
    and certify-by dates based on severity SLA."""
    items: list[dict] = []

    for v in violations:
        sla = SEVERITY_SLA.get(v.severity, {"days": 30})
        if "hours" in sla:
            certify_by = datetime.now(timezone.utc) + timedelta(hours=sla["hours"])
        else:
            certify_by = datetime.now(timezone.utc) + timedelta(days=sla.get("days", 30))

        action = _determine_action(v)

        items.append({
            "violation_id": v.violation_id,
            "type": v.type.value,
            "severity": v.severity.value,
            "description": v.description,
            "affected_accounts": v.affected_accounts,
            "control_id": v.control_mapping.get("control_id", ""),
            "action": action,
            "certify_by": certify_by.isoformat(),
            "certified_by": "",
            "remediation": v.remediation,
        })

    return items


def _determine_action(violation: Violation) -> str:
    """Map violation type to a certification action."""
    type_action = {
        "LEAVER_ACTIVE": "REVOKE",
        "ORPHANED": "REVOKE",
        "MFA_MISSING": "REVIEW",
        "SELF_APPROVAL": "REVIEW",
    }
    return type_action.get(violation.type.value, "REVIEW")


def format_summary(violations: list[Violation]) -> dict:
    """Count violations by severity and type."""
    by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
    by_type: dict[str, int] = {}

    for v in violations:
        by_severity[v.severity.value] += 1
        t = v.type.value
        by_type[t] = by_type.get(t, 0) + 1

    return {
        "total": len(violations),
        "by_severity": by_severity,
        "by_type": by_type,
    }


def build_audit_report(
    violations: list[Violation],
    ad_count: int,
    hr_count: int,
    itsm_count: int,
) -> AuditReport:
    """Build the full AuditReport from violations and scope info."""
    summary = format_summary(violations)
    cert_items = generate_access_certification(violations)

    return AuditReport(
        audit_date=datetime.now(timezone.utc).isoformat(),
        scope=f"{ad_count} AD accounts, {hr_count} HR records, {itsm_count} ITSM tickets reviewed",
        summary=summary,
        violations=violations,
        access_certification_items=cert_items,
    )


def export_json(report: AuditReport, output_path: Path) -> Path:
    """Export the audit report as structured JSON."""
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


def _ragged_paragraph(text, style):
    """Wrap multi-line account names into a <br/>-joined Paragraph."""
    from reportlab.platypus import Paragraph
    if isinstance(text, list):
        text = "<br/>".join(str(t) for t in text)
    return Paragraph(str(text), style)


def _on_page(canvas, doc):
    """Draw footer on every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor("#999999")
    canvas.drawString(1.5 * 72 / 2.54, 1.2 * 72 / 2.54,
                      "IAM Access Lifecycle Simulator — GRC Portfolio | CONFIDENTIAL")
    canvas.drawRightString(21 * 72 / 2.54 - 1.5 * 72 / 2.54, 1.2 * 72 / 2.54,
                           f"Page {doc.page}")
    canvas.restoreState()


def export_pdf(report: AuditReport, output_path: Path) -> Path:
    """Generate a professional PDF audit report using ReportLab.

    All table cells use Paragraph objects so text wraps correctly within
    column boundaries. Follows P5 reporter.py conventions.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.colors import HexColor
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT
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

    # Shared cell styles
    cell_body = ParagraphStyle(
        "IAMCellBody", parent=styles["Normal"],
        fontSize=7.5, leading=10, wordWrap="CJK",
    )
    cell_bold = ParagraphStyle(
        "IAMCellBold", parent=cell_body,
        fontName="Helvetica-Bold",
    )
    cell_hdr = ParagraphStyle(
        "IAMCellHdr", parent=cell_body,
        fontName="Helvetica-Bold", fontSize=7.5, leading=10,
        textColor=HexColor("#FFFFFF"),
    )
    cell_sm = ParagraphStyle(
        "IAMCellSm", parent=cell_body,
        fontSize=7, leading=9, wordWrap="CJK",
    )
    body_text = ParagraphStyle(
        "IAMBodyText", parent=styles["Normal"],
        fontSize=9, leading=13,
    )

    VODAFONE_RED = HexColor("#E60000")
    RAG_GREEN_BG = HexColor("#D4EDDA")
    RAG_AMBER_BG = HexColor("#FFF3CD")
    RAG_RED_BG = HexColor("#F8D7DA")
    HEADER_BG = VODAFONE_RED
    DARK_GREY = HexColor("#333333")
    ROW_A = HexColor("#FFFFFF")
    ROW_B = HexColor("#FAFAFA")
    BORDER = HexColor("#CCCCCC")

    sev_bg_map = {
        "CRITICAL": RAG_RED_BG,
        "HIGH": RAG_AMBER_BG,
        "MEDIUM": RAG_GREEN_BG,
    }

    story = []

    # ── Cover ──────────────────────────────────────────────────
    story.append(Paragraph(
        "IAM Access Lifecycle Audit Report",
        ParagraphStyle("IAMTitle", parent=styles["Title"], fontSize=20, leading=24,
                       textColor=VODAFONE_RED, spaceAfter=4),
    ))
    date_display = report.audit_date[:19].replace("T", " ") if "T" in report.audit_date else report.audit_date
    story.append(Paragraph(
        f"Vodafone GRC — Access Lifecycle Simulator<br/>"
        f"Date: {date_display} UTC",
        ParagraphStyle("IAMSubtitle", parent=styles["Normal"], fontSize=9,
                       textColor=HexColor("#666666"), spaceAfter=10),
    ))
    story.append(HRFlowable(width="100%", color=VODAFONE_RED, thickness=1.5))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        f"<b>Scope:</b> {report.scope}",
        ParagraphStyle("IAMScope", parent=styles["Normal"], fontSize=9,
                       textColor=DARK_GREY, spaceAfter=4),
    ))
    story.append(Paragraph(
        f"<b>Audit Date:</b> {date_display} UTC",
        ParagraphStyle("IAMDate", parent=styles["Normal"], fontSize=9,
                       textColor=DARK_GREY, spaceAfter=4),
    ))
    story.append(Spacer(1, 0.5 * cm))

    # ── Executive Summary ──────────────────────────────────────
    story.append(Paragraph("Executive Summary", ParagraphStyle(
        "IAMH2", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=DARK_GREY,
    )))
    s = report.summary
    by_sev = s["by_severity"]
    by_type = s["by_type"]

    # Severity breakdown table
    sev_rows = [
        _hdr_row(["Total Violations", "CRITICAL", "HIGH", "MEDIUM"], cell_hdr),
        [
            _p(str(s["total"]), cell_bold),
            _p(str(by_sev["CRITICAL"]), cell_bold),
            _p(str(by_sev["HIGH"]), cell_bold),
            _p(str(by_sev["MEDIUM"]), cell_bold),
        ],
    ]
    sev_table = Table(sev_rows, colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm, 4.5 * cm])
    sev_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A]),
    ]
    # Colour severity cells
    sev_style.append(("BACKGROUND", (1, 1), (1, 1), RAG_RED_BG))
    sev_style.append(("BACKGROUND", (2, 1), (2, 1), RAG_AMBER_BG))
    sev_style.append(("BACKGROUND", (3, 1), (3, 1), RAG_GREEN_BG))
    sev_table.setStyle(TableStyle(sev_style))
    story.append(sev_table)
    story.append(Spacer(1, 0.4 * cm))

    # By-type breakdown table
    type_rows = [_hdr_row(["Violation Type", "Count"], cell_hdr)]
    for vtype, count in sorted(by_type.items()):
        type_rows.append([_p(vtype, cell_body), _p(str(count), cell_bold)])
    type_table = Table(type_rows, colWidths=[13 * cm, 5 * cm])
    type_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
    ]))
    story.append(type_table)
    story.append(Spacer(1, 0.6 * cm))

    # ── Violations Detail ──────────────────────────────────────
    story.append(Paragraph("Violations Detail", ParagraphStyle(
        "IAMH2b", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=DARK_GREY,
    )))

    if report.violations:
        v_rows = [_hdr_row(["ID", "Type", "Severity", "Description", "Affected Accounts",
                            "Control ID", "Remediation"], cell_hdr)]
        for v in report.violations:
            sev_val = v.severity.value if hasattr(v.severity, 'value') else str(v.severity)
            type_val = v.type.value if hasattr(v.type, 'value') else str(v.type)
            v_rows.append([
                _p(v.violation_id, cell_sm),
                _p(type_val, cell_body),
                _p(sev_val, cell_bold),
                _p(v.description, cell_body),
                _ragged_paragraph(v.affected_accounts, cell_sm),
                _p(v.control_mapping.get("control_id", ""), cell_body),
                _p(v.remediation, cell_sm),
            ])

        v_table = Table(v_rows, colWidths=[2 * cm, 2.5 * cm, 2 * cm, 3.5 * cm,
                                            3 * cm, 2 * cm, 3 * cm])
        v_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ]
        # Colour severity column
        for i, v in enumerate(report.violations, 1):
            sev_val = v.severity.value if hasattr(v.severity, 'value') else str(v.severity)
            bg = sev_bg_map.get(sev_val, ROW_A)
            v_style.append(("BACKGROUND", (2, i), (2, i), bg))
        v_table.setStyle(TableStyle(v_style))
        story.append(v_table)
    else:
        story.append(Paragraph(
            "<i>No violations found. All controls passed.</i>",
            ParagraphStyle("IAMNoFindings", parent=styles["Normal"], fontSize=9,
                           textColor=HexColor("#666666"), spaceAfter=4),
        ))
    story.append(Spacer(1, 0.6 * cm))

    # ── Access Certification ───────────────────────────────────
    if report.access_certification_items:
        story.append(PageBreak())
        story.append(Paragraph("Access Certification", ParagraphStyle(
            "IAMH2c", parent=styles["Heading2"], fontSize=13, leading=16,
            spaceBefore=12, spaceAfter=6, textColor=DARK_GREY,
        )))
        cert_rows = [_hdr_row(["Action", "Account", "Certify By", "Control ID", "Type"], cell_hdr)]
        for item in report.access_certification_items:
            account = item["affected_accounts"][0] if item["affected_accounts"] else "N/A"
            cert_by = item["certify_by"][:19].replace("T", " ") if "T" in item["certify_by"] else item["certify_by"]
            cert_rows.append([
                _p(item["action"], cell_bold),
                _p(account, cell_body),
                _p(cert_by, cell_body),
                _p(item.get("control_id", ""), cell_body),
                _p(item.get("type", ""), cell_sm),
            ])
        cert_table = Table(cert_rows, colWidths=[2.5 * cm, 4 * cm, 4 * cm, 3 * cm, 4.5 * cm])
        cert_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
        ]
        # Colour REVOKE rows with light red background
        for i, item in enumerate(report.access_certification_items, 1):
            if item["action"] == "REVOKE":
                cert_style.append(("BACKGROUND", (0, i), (-1, i), RAG_RED_BG))
        cert_table.setStyle(TableStyle(cert_style))
        story.append(cert_table)
        story.append(Spacer(1, 0.6 * cm))

    # ── SLA Reference ──────────────────────────────────────────
    story.append(Paragraph("SLA Reference", ParagraphStyle(
        "IAMH2d", parent=styles["Heading2"], fontSize=13, leading=16,
        spaceBefore=12, spaceAfter=6, textColor=DARK_GREY,
    )))
    sla_rows = [_hdr_row(["Severity", "SLA"], cell_hdr)]
    sla_rows.append([_p("CRITICAL", cell_bold), _p("24 hours", cell_body)])
    sla_rows.append([_p("HIGH", cell_bold), _p("7 days", cell_body)])
    sla_rows.append([_p("MEDIUM", cell_bold), _p("30 days", cell_body)])
    sla_table = Table(sla_rows, colWidths=[9 * cm, 9 * cm])
    sla_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
    ]
    # Colour the severity column
    sla_style.append(("BACKGROUND", (0, 1), (0, 1), RAG_RED_BG))
    sla_style.append(("BACKGROUND", (0, 2), (0, 2), RAG_AMBER_BG))
    sla_style.append(("BACKGROUND", (0, 3), (0, 3), RAG_GREEN_BG))
    sla_table.setStyle(TableStyle(sla_style))
    story.append(sla_table)

    # ── Build with footer callback ─────────────────────────────
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return output_path
