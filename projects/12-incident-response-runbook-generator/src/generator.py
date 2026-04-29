"""Runbook generation engine.

Orchestrates template selection, AI customisation, and output formatting.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    Runbook, RunbookTemplate, IRStage, Severity, INCIDENT_TYPE_LABELS, SEVERITY_SLA,
)
from .templates import TEMPLATES
from .ai_customizer import customize_runbook, enrich_with_regulatory


def generate_runbook(
    incident_type: str,
    severity: str,
    context: dict | None = None,
) -> Runbook:
    """Full pipeline: select template, customise, assemble runbook.

    Args:
        incident_type: One of malware, ransomware, breach, ddos, insider, credential.
        severity: SEV1, SEV2, or SEV3.
        context: Organisation context dict (org_name, industry, regulatory_reqs, etc.).

    Returns:
        A fully assembled Runbook.
    """
    if context is None:
        context = {}

    template = TEMPLATES.get(incident_type)
    if template is None:
        raise ValueError(f"Unknown incident type: {incident_type}. Available: {list(TEMPLATES.keys())}")

    sev = Severity(severity)

    # Customise the template with AI
    customised = customize_runbook(template, context)

    # Adjust SLAs based on severity
    sla_overrides = SEVERITY_SLA.get(sev, SEVERITY_SLA[Severity.SEV2])
    stages: list[IRStage] = []
    for stage in customised["stages"]:
        adjusted_sla = _adjust_sla_for_severity(stage.sla_minutes, sev)
        stages.append(IRStage(
            stage_number=stage.stage_number,
            stage_name=stage.stage_name,
            description=stage.description,
            actions=stage.actions,
            responsible_team=stage.responsible_team,
            sla_minutes=adjusted_sla,
            escalation_trigger=stage.escalation_trigger,
        ))

    # Add regulatory actions to post-incident stages
    regs = context.get("regulatory_reqs", [])
    if regs:
        regulatory_actions = enrich_with_regulatory(regs)
        for stage in stages:
            if stage.stage_number == 5:  # Post-Incident Analysis
                stage.actions.extend(regulatory_actions[:4])
            elif stage.stage_number == 6:  # Lessons Learned
                stage.actions.extend(regulatory_actions[4:])

    # Build recovery objectives based on severity
    rto_hours = {Severity.SEV1: 4, Severity.SEV2: 8, Severity.SEV3: 24}.get(sev, 8)
    rpo_hours = {Severity.SEV1: 1, Severity.SEV2: 4, Severity.SEV3: 12}.get(sev, 4)

    org_name = context.get("org_name", "Organisation")

    runbook = Runbook(
        incident_type=incident_type,
        severity=sev,
        generated_date=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        organization=org_name,
        stages=stages,
        contacts=customised["contacts"],
        tools=customised["tools"],
        communication_plan=customised["communication_plan"],
        recovery_objectives={
            "rto_hours": rto_hours,
            "rpo_hours": rpo_hours,
        },
        lessons_learned_prompt=_build_lessons_learned_prompt(incident_type, severity, org_name),
    )

    return runbook


def generate_all(context: dict | None = None) -> list[Runbook]:
    """Generate all 6 runbooks for a given context."""
    runbooks: list[Runbook] = []
    for incident_type in TEMPLATES:
        # Use SEV2 as default for batch generation
        runbooks.append(generate_runbook(incident_type, "SEV2", context))
    return runbooks


def export_runbook_markdown(runbook: Runbook) -> str:
    """Export a runbook as a full markdown document.

    Includes headings, checkboxes for actions, tables for contacts/tools/SLAs,
    and structured sections that an incident responder can follow step by step.
    """
    sev = runbook.severity.value
    label = INCIDENT_TYPE_LABELS.get(runbook.incident_type, runbook.incident_type)
    sla = SEVERITY_SLA.get(runbook.severity, SEVERITY_SLA[Severity.SEV2])

    lines: list[str] = []
    lines.append(f"# Incident Response Runbook: {label}")
    lines.append("")
    lines.append(f"**Organisation:** {runbook.organization}  ")
    lines.append(f"**Incident Type:** {label}  ")
    lines.append(f"**Severity:** {sev}  ")
    lines.append(f"**Generated:** {runbook.generated_date}  ")
    lines.append(f"**Total Stages:** {len(runbook.stages)}  ")
    lines.append(f"**Total Actions:** {runbook.total_actions}  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Severity SLA summary
    lines.append("## Severity SLA")
    lines.append("")
    lines.append(f"| Metric | Target |")
    lines.append(f"|--------|--------|")
    lines.append(f"| Response Time | {sla['response']} minutes |")
    lines.append(f"| Containment Time | {sla['containment']} minutes |")
    lines.append(f"| Resolution Time | {sla['resolution']} minutes |")
    lines.append("")

    # Recovery Objectives
    lines.append("## Recovery Objectives")
    lines.append("")
    lines.append(f"- **Recovery Time Objective (RTO):** {runbook.recovery_objectives.get('rto_hours', 'N/A')} hours")
    lines.append(f"- **Recovery Point Objective (RPO):** {runbook.recovery_objectives.get('rpo_hours', 'N/A')} hours")
    lines.append("")

    # Contacts
    lines.append("## Key Contacts")
    lines.append("")
    lines.append(f"| Role | Name | Email | Phone |")
    lines.append(f"|------|------|-------|-------|")
    for role, info in runbook.contacts.items():
        lines.append(f"| {role} | {info.get('name', 'N/A')} | {info.get('email', 'N/A')} | {info.get('phone', 'N/A')} |")
    lines.append("")

    # Tools
    lines.append("## Tools & Systems")
    lines.append("")
    lines.append(f"| Tool | Purpose |")
    lines.append(f"|------|---------|")
    for tool in runbook.tools:
        lines.append(f"| {tool.get('name', 'N/A')} | {tool.get('purpose', 'N/A')} |")
    lines.append("")

    # Communication Plan
    lines.append("## Communication Plan")
    lines.append("")
    for comm in runbook.communication_plan:
        lines.append(f"- {comm}")
    lines.append("")

    # IR Stages
    lines.append("## Incident Response Stages")
    lines.append("")
    for stage in runbook.stages:
        lines.append(f"### Stage {stage.stage_number}: {stage.stage_name}")
        lines.append("")
        lines.append(f"**Description:** {stage.description}  ")
        lines.append(f"**Responsible Team:** {stage.responsible_team}  ")
        lines.append(f"**SLA:** {stage.sla_minutes} minutes  ")
        lines.append(f"**Escalation Trigger:** {stage.escalation_trigger}  ")
        lines.append("")
        lines.append("**Actions:**")
        lines.append("")
        for action in stage.actions:
            lines.append(f"- [ ] {action}")
        lines.append("")

    # Lessons Learned Prompt
    lines.append("## Lessons Learned")
    lines.append("")
    lines.append(runbook.lessons_learned_prompt)
    lines.append("")

    lines.append("---")
    lines.append(f"*Runbook generated by Incident Response Runbook Generator on {runbook.generated_date}*")
    lines.append("")

    return "\n".join(lines)


def export_runbook_json(runbook: Runbook) -> str:
    """Export a runbook as structured JSON."""
    return json.dumps(runbook.to_dict(), indent=2)


def save_runbook(runbook: Runbook, output_dir: Path, format: str = "md") -> list[Path]:
    """Save a runbook to the specified directory in markdown, JSON, and/or PDF format.

    Args:
        runbook: The Runbook to save.
        output_dir: Directory to save files in.
        format: "md", "json", "pdf", "both" (md+json), or "all" (md+json+pdf).

    Returns:
        List of saved file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    sev = runbook.severity.value.lower()
    incident_type = runbook.incident_type
    saved: list[Path] = []

    _save_md = format in ("md", "both", "all")
    _save_json = format in ("json", "both", "all")
    _save_pdf = format in ("pdf", "all")

    if _save_md:
        md_path = output_dir / f"{incident_type}-{sev}-runbook.md"
        md_path.write_text(export_runbook_markdown(runbook))
        saved.append(md_path)

    if _save_json:
        json_path = output_dir / f"{incident_type}-{sev}-runbook.json"
        json_path.write_text(export_runbook_json(runbook))
        saved.append(json_path)

    if _save_pdf:
        pdf_path = output_dir / f"{incident_type}-{sev}-runbook.pdf"
        export_runbook_pdf(runbook, str(pdf_path))
        saved.append(pdf_path)

    return saved


# ─────────────────────────────────────────────────────────────────
# PDF export
# ─────────────────────────────────────────────────────────────────

def _p(text, style):
    """Wrap text in a ReportLab Paragraph so it word-wraps inside table cells."""
    from reportlab.platypus import Paragraph
    return Paragraph(str(text), style)


def _hdr_row(labels, style):
    """Build a header row of bold Paragraph cells."""
    return [_p(l, style) for l in labels]


def export_runbook_pdf(runbook: Runbook, output_path: str) -> str:
    """Generate a professional PDF runbook using ReportLab.

    Follows the P5 reporter.py pattern for colours, styles, and layout.
    All table cells use Paragraph objects so text wraps correctly within
    column boundaries.
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

    # ── Shared data ──────────────────────────────────────────────
    sev = runbook.severity.value
    label = INCIDENT_TYPE_LABELS.get(runbook.incident_type, runbook.incident_type)
    label_upper = label.upper()

    sev_bg_map = {
        "SEV1": HexColor("#F8D7DA"),
        "SEV2": HexColor("#FFF3CD"),
        "SEV3": HexColor("#D4EDDA"),
    }
    sev_text_map = {
        "SEV1": "CRITICAL — SEV1",
        "SEV2": "HIGH — SEV2",
        "SEV3": "MODERATE — SEV3",
    }

    VODAFONE_RED = HexColor("#E60000")
    SEV_BG = sev_bg_map.get(sev, HexColor("#FFF3CD"))
    HEADER_BG = VODAFONE_RED
    DARK_GREY = HexColor("#333333")
    LESSONS_BG = HexColor("#F5F5F5")
    ROW_A = HexColor("#FFFFFF")
    ROW_B = HexColor("#FAFAFA")
    BORDER = HexColor("#CCCCCC")
    LABEL_BG = HexColor("#F5F5F5")

    # ── Document setup ───────────────────────────────────────────
    styles = getSampleStyleSheet()

    ir_title = ParagraphStyle(
        "IRTitle", parent=styles["Title"],
        fontSize=22, leading=28, textColor=VODAFONE_RED,
        spaceAfter=6, alignment=TA_CENTER,
    )
    ir_subtitle = ParagraphStyle(
        "IRSubtitle", parent=styles["Normal"],
        fontSize=18, leading=22, textColor=VODAFONE_RED,
        spaceAfter=4, alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    ir_h2 = ParagraphStyle(
        "IRH2", parent=styles["Heading2"],
        fontSize=13, leading=16, textColor=DARK_GREY,
        spaceBefore=12, spaceAfter=6,
    )
    ir_h3 = ParagraphStyle(
        "IRH3", parent=styles["Heading2"],
        fontSize=14, leading=18, textColor=VODAFONE_RED,
        spaceBefore=10, spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    ir_body = ParagraphStyle(
        "IRBody", parent=styles["Normal"],
        fontSize=9, leading=13,
    )
    ir_cell_body = ParagraphStyle(
        "IRCellBody", parent=styles["Normal"],
        fontSize=8, leading=11, wordWrap="CJK",
    )
    ir_cell_bold = ParagraphStyle(
        "IRCellBold", parent=ir_cell_body,
        fontName="Helvetica-Bold",
    )
    ir_cell_hdr = ParagraphStyle(
        "IRCellHdr", parent=ir_cell_body,
        fontName="Helvetica-Bold", fontSize=8, leading=11,
        textColor=HexColor("#FFFFFF"),
    )
    ir_cell_sm = ParagraphStyle(
        "IRCellSm", parent=ir_cell_body,
        fontSize=7.5, leading=10, wordWrap="CJK",
    )
    ir_cover_label = ParagraphStyle(
        "IRCoverLabel", parent=styles["Normal"],
        fontSize=24, leading=30, textColor=VODAFONE_RED,
        fontName="Helvetica-Bold", alignment=TA_CENTER,
        spaceAfter=12,
    )

    # ── Page footer callback ─────────────────────────────────────
    def _page_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor("#999999"))
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(1.5 * cm, 1.2 * cm, A4[0] - 1.5 * cm, 1.2 * cm)
        canvas.drawString(
            1.5 * cm, 0.8 * cm,
            "Incident Response Runbook Generator — GRC Portfolio | CONFIDENTIAL",
        )
        canvas.drawCentredString(A4[0] / 2, 0.8 * cm, label)
        canvas.drawRightString(
            A4[0] - 1.5 * cm, 0.8 * cm, f"Page {canvas.getPageNumber()}",
        )
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2.5 * cm,
        title=f"IR Runbook: {label} ({sev})",
        author=runbook.organization,
    )

    story: list = []

    # ── 1. Cover page ────────────────────────────────────────────
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("INCIDENT RESPONSE RUNBOOK", ir_title))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(label_upper, ir_cover_label))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="60%", color=VODAFONE_RED, thickness=2))

    # Severity badge
    sev_table = Table(
        [[_p(sev_text_map.get(sev, sev), ir_cell_bold)]],
        colWidths=[8 * cm],
    )
    sev_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SEV_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("BOX", (0, 0), (-1, -1), 1.5, VODAFONE_RED),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))
    cover_meta = [
        [sev_table],
    ]
    cover_meta_table = Table(cover_meta, colWidths=[16 * cm])
    cover_meta_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(cover_meta_table)
    story.append(Spacer(1, 1 * cm))

    # Organisation meta
    org_meta = [
        [_p("Organisation", ir_cell_bold), _p(runbook.organization, ir_cell_body)],
        [_p("Generated", ir_cell_bold), _p(runbook.generated_date, ir_cell_body)],
        [_p("Incident Type", ir_cell_bold), _p(label, ir_cell_body)],
        [_p("Severity", ir_cell_bold), _p(sev, ir_cell_bold)],
        [_p("Recovery Objectives", ir_cell_bold),
         _p(f"RTO: {runbook.recovery_objectives.get('rto_hours', 'N/A')} hours  |  "
            f"RPO: {runbook.recovery_objectives.get('rpo_hours', 'N/A')} hours",
            ir_cell_body)],
    ]
    org_meta_table = Table(org_meta, colWidths=[4.5 * cm, 11.5 * cm])
    org_meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LABEL_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(org_meta_table)

    # ── 2. Key Metrics ───────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Key Metrics", ir_h2))
    story.append(Spacer(1, 0.2 * cm))

    total_sla = runbook.total_sla_minutes
    metrics_data = [
        _hdr_row(["Metric", "Value"], ir_cell_hdr),
        [_p("RTO (Recovery Time Objective)", ir_cell_body),
         _p(f"{runbook.recovery_objectives.get('rto_hours', 'N/A')} hours", ir_cell_bold)],
        [_p("RPO (Recovery Point Objective)", ir_cell_body),
         _p(f"{runbook.recovery_objectives.get('rpo_hours', 'N/A')} hours", ir_cell_bold)],
        [_p("Total Stages", ir_cell_body),
         _p(str(len(runbook.stages)), ir_cell_bold)],
        [_p("Total Actions", ir_cell_body),
         _p(str(runbook.total_actions), ir_cell_bold)],
        [_p("Total SLA Minutes", ir_cell_body),
         _p(str(total_sla), ir_cell_bold)],
    ]
    metrics_table = Table(metrics_data, colWidths=[10 * cm, 6 * cm])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
    ]))
    story.append(metrics_table)

    # ── 3. SLA Reference table ───────────────────────────────────
    story.append(Spacer(1, 0.7 * cm))
    story.append(Paragraph("SLA Reference", ir_h2))
    story.append(Spacer(1, 0.2 * cm))

    sla_rows = [_hdr_row(["Stage #", "Stage Name", "SLA (min)", "Responsible Team"], ir_cell_hdr)]
    for stage in runbook.stages:
        sla_rows.append([
            _p(str(stage.stage_number), ir_cell_bold),
            _p(stage.stage_name, ir_cell_body),
            _p(str(stage.sla_minutes), ir_cell_body),
            _p(stage.responsible_team, ir_cell_sm),
        ])
    sla_table = Table(sla_rows, colWidths=[1.5 * cm, 4.5 * cm, 2.5 * cm, 7.5 * cm])
    sla_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
    ]))
    story.append(sla_table)

    # ── 4. Contacts table ────────────────────────────────────────
    story.append(Spacer(1, 0.7 * cm))
    story.append(Paragraph("Key Contacts", ir_h2))
    story.append(Spacer(1, 0.2 * cm))

    contact_rows = [_hdr_row(["Role", "Name", "Email", "Phone"], ir_cell_hdr)]
    for role, info in runbook.contacts.items():
        contact_rows.append([
            _p(role, ir_cell_bold),
            _p(info.get("name", "N/A"), ir_cell_body),
            _p(info.get("email", "N/A"), ir_cell_sm),
            _p(info.get("phone", "N/A"), ir_cell_body),
        ])
    contact_table = Table(contact_rows, colWidths=[3.5 * cm, 3.5 * cm, 5 * cm, 4 * cm])
    contact_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
    ]))
    story.append(contact_table)

    # ── 5. Tools & Systems table ─────────────────────────────────
    story.append(Spacer(1, 0.7 * cm))
    story.append(Paragraph("Tools &amp; Systems", ir_h2))
    story.append(Spacer(1, 0.2 * cm))

    tool_rows = [_hdr_row(["Tool Name", "Purpose"], ir_cell_hdr)]
    for tool in runbook.tools:
        tool_rows.append([
            _p(tool.get("name", "N/A"), ir_cell_bold),
            _p(tool.get("purpose", "N/A"), ir_cell_body),
        ])
    tool_table = Table(tool_rows, colWidths=[5 * cm, 11 * cm])
    tool_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
    ]))
    story.append(tool_table)

    # ── 6. Communication Plan ────────────────────────────────────
    story.append(Spacer(1, 0.7 * cm))
    story.append(Paragraph("Communication Plan", ir_h2))
    story.append(Spacer(1, 0.2 * cm))

    comm_rows = [_hdr_row(["#", "Action"], ir_cell_hdr)]
    for i, action in enumerate(runbook.communication_plan, 1):
        comm_rows.append([
            _p(str(i), ir_cell_bold),
            _p(action, ir_cell_body),
        ])
    comm_table = Table(comm_rows, colWidths=[1.2 * cm, 14.8 * cm])
    comm_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
    ]))
    story.append(comm_table)

    # ── 7. Per-Stage Runbook ─────────────────────────────────────
    for stage in runbook.stages:
        story.append(PageBreak())

        # Stage header
        story.append(Paragraph(
            f"Stage {stage.stage_number}: {stage.stage_name}",
            ir_h3,
        ))
        story.append(HRFlowable(width="100%", color=VODAFONE_RED, thickness=1))

        # Info box
        info_rows = [
            [_p("Description", ir_cell_bold),
             _p(stage.description, ir_cell_body)],
            [_p("Responsible Team", ir_cell_bold),
             _p(stage.responsible_team, ir_cell_body)],
            [_p("SLA", ir_cell_bold),
             _p(f"{stage.sla_minutes} minutes", ir_cell_bold)],
            [_p("Escalation Trigger", ir_cell_bold),
             _p(stage.escalation_trigger, ir_cell_sm)],
        ]
        info_table = Table(info_rows, colWidths=[4 * cm, 12 * cm])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LABEL_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5 * cm))

        # Action Checklist
        story.append(Paragraph("Action Checklist", ParagraphStyle(
            "IRH4", parent=ir_h2, fontSize=11, leading=14, spaceBefore=4, spaceAfter=4,
        )))

        action_rows = [_hdr_row(["", "Action"], ir_cell_hdr)]
        for i, action in enumerate(stage.actions, 1):
            action_rows.append([
                _p("[  ]", ir_cell_body),  # checkbox
                _p(f"{i}. {action}", ir_cell_body),
            ])
        action_table = Table(action_rows, colWidths=[1.2 * cm, 14.8 * cm])
        action_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ]))
        story.append(action_table)

    # ── 8. Recovery Objectives ───────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Recovery Objectives", ir_h2))
    story.append(Spacer(1, 0.2 * cm))

    rto = runbook.recovery_objectives.get("rto_hours", "N/A")
    rpo = runbook.recovery_objectives.get("rpo_hours", "N/A")
    recovery_rows = [
        [_p("Recovery Time Objective (RTO)", ir_cell_bold),
         _p(f"{rto} hours", ir_cell_body)],
        [_p("Definition", ir_cell_bold),
         _p("Maximum acceptable time to restore business operations after an incident is declared.",
            ir_cell_body)],
        [_p("Recovery Point Objective (RPO)", ir_cell_bold),
         _p(f"{rpo} hours", ir_cell_body)],
        [_p("Definition", ir_cell_bold),
         _p("Maximum acceptable data loss measured in time. Backups must be taken at intervals "
            "shorter than this window.", ir_cell_body)],
    ]
    recovery_table = Table(recovery_rows, colWidths=[5 * cm, 11 * cm])
    recovery_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LABEL_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(recovery_table)

    # ── 9. Lessons Learned Prompt ────────────────────────────────
    story.append(Spacer(1, 0.7 * cm))
    story.append(Paragraph("Lessons Learned", ir_h2))
    story.append(Spacer(1, 0.2 * cm))

    lessons_data = [
        [_p(runbook.lessons_learned_prompt, ir_cell_body)],
    ]
    lessons_table = Table(lessons_data, colWidths=[16 * cm])
    lessons_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LESSONS_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(lessons_table)

    # ── End spacer ───────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return str(output_path)


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _adjust_sla_for_severity(base_sla: int, severity: Severity) -> int:
    """Adjust SLA minutes based on severity level."""
    if severity == Severity.SEV1:
        # SEV1: compress SLAs to 50% of base
        return max(5, int(base_sla * 0.5))
    elif severity == Severity.SEV3:
        # SEV3: relax SLAs to 150% of base
        return int(base_sla * 1.5)
    return base_sla


def _build_lessons_learned_prompt(incident_type: str, severity: str, org_name: str) -> str:
    """Build a structured lessons-learned prompt for post-incident review."""
    label = INCIDENT_TYPE_LABELS.get(incident_type, incident_type)

    prompts: dict[str, str] = {
        "malware": (
            f"Review the Malware Outbreak incident at {org_name} (Severity: {severity}). "
            "Document: (1) How did the malware enter the environment? "
            "(2) Which controls failed to detect it? "
            "(3) How effective was the containment -- did lateral movement occur? "
            "(4) Were backups clean and restorable? "
            "(5) What new IOCs should be added to detection tooling? "
            "(6) How can user awareness training be improved to reduce future risk?"
        ),
        "ransomware": (
            f"Review the Ransomware Attack incident at {org_name} (Severity: {severity}). "
            "Document: (1) What was the initial access vector? "
            "(2) How quickly was encryption detected and contained? "
            "(3) Was backup infrastructure protected from encryption? "
            "(4) Was data exfiltrated before encryption (double extortion)? "
            "(5) Was the ransom paid? If so, did decryption work? "
            "(6) What improvements are needed for offline/immutable backups, AD hardening, and email security?"
        ),
        "breach": (
            f"Review the Data Breach incident at {org_name} (Severity: {severity}). "
            "Document: (1) What data was exfiltrated and how was it accessed? "
            "(2) Were regulatory notification deadlines met (GDPR 72h, PCI-DSS 24h)? "
            "(3) Was the breached data encrypted at rest and in transit? "
            "(4) How effective were DLP controls at preventing exfiltration? "
            "(5) What was the root cause: misconfiguration, compromised credentials, insider, or application vulnerability? "
            "(6) What improvements are needed for data classification, access control, and monitoring?"
        ),
        "ddos": (
            f"Review the DDoS Attack incident at {org_name} (Severity: {severity}). "
            "Document: (1) What was the attack vector and peak volume? "
            "(2) How effective was the DDoS mitigation provider? "
            "(3) Were legitimate users able to access the service during mitigation? "
            "(4) What was the total downtime and estimated revenue impact? "
            "(5) Was there a companion attack (data breach, social engineering)? "
            "(6) Is current DDoS protection capacity adequate for future attacks?"
        ),
        "insider": (
            f"Review the Insider Threat incident at {org_name} (Severity: {severity}). "
            "Document: (1) What was the insider's motive and method? "
            "(2) What data or systems were affected? "
            "(3) Were HR trigger events missed that could have provided early warning? "
            "(4) How effective were UEBA, DLP, and access controls at detecting and preventing the incident? "
            "(5) Was the offboarding process executed completely and timely? "
            "(6) What improvements are needed for background checks, privilege management, and monitoring?"
        ),
        "credential": (
            f"Review the Credential Theft incident at {org_name} (Severity: {severity}). "
            "Document: (1) How were the credentials compromised (phishing, credential stuffing, MFA fatigue, token theft)? "
            "(2) What was the privilege level of the compromised account? "
            "(3) How quickly was the compromise detected and the account locked? "
            "(4) Did the attacker achieve lateral movement or persistence? "
            "(5) Was MFA bypassed or not enforced for the affected account? "
            "(6) What improvements are needed for MFA enforcement, password policy, breached password detection, and phishing-resistant authentication?"
        ),
    }

    return prompts.get(incident_type, f"Review the {label} incident at {org_name} (Severity: {severity}). Document root cause, control failures, response effectiveness, and improvement actions.")
