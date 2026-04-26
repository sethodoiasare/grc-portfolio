"""
Report Generator

Produces three output formats from a list of AssessmentResult objects:

  1. JSON report  — structured dict suitable for machine consumption or filing
  2. Rich table   — colour-coded CLI summary printed to stdout
  3. PDF report   — professional A4 document with Vodafone branding, executive
                    summary, results table, and full finding narratives

The module has no side-effects on import; all output is triggered explicitly
by calling the appropriate method on a ReportGenerator instance.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table as RLTable,
    TableStyle,
    HRFlowable,
    PageBreak,
)

from src.models import AssessmentResult, Verdict, RiskRating


# ---------------------------------------------------------------------------
# Colour maps
# ---------------------------------------------------------------------------

VERDICT_COLOUR: dict[Verdict, str] = {
    Verdict.PASS: "green",
    Verdict.PARTIAL: "yellow",
    Verdict.FAIL: "red",
    Verdict.INSUFFICIENT_EVIDENCE: "dim",
}

RISK_COLOUR: dict[RiskRating, str] = {
    RiskRating.CRITICAL: "red",
    RiskRating.HIGH: "dark_orange",
    RiskRating.MEDIUM: "yellow",
    RiskRating.LOW: "cyan",
    RiskRating.INFORMATIONAL: "dim",
}

# Pastel background colours used in the PDF results table
_PDF_VERDICT_BG: dict[str, object] = {
    "PASS": colors.HexColor("#D4EDDA"),
    "PARTIAL": colors.HexColor("#FFF3CD"),
    "FAIL": colors.HexColor("#F8D7DA"),
    "INSUFFICIENT_EVIDENCE": colors.HexColor("#E2E3E5"),
}

# Vodafone brand colours
_VODAFONE_RED = colors.HexColor("#E60000")
_DARK_GREY = colors.HexColor("#333333")
_LIGHT_GREY = colors.HexColor("#F5F5F5")


class ReportGenerator:
    """
    Stateless report renderer.  A single instance can be reused across many
    report generation calls without any shared mutable state.
    """

    # ------------------------------------------------------------------
    # 1. JSON report
    # ------------------------------------------------------------------

    def generate_json_report(
        self,
        results: list[AssessmentResult],
        audit_scope: str,
        report_id: Optional[str] = None,
    ) -> dict:
        """
        Produce a fully structured JSON-serialisable report dict.

        The report contains:
          - Metadata (report_id, timestamp, scope)
          - Executive summary with pass rate and RAG status
          - findings array (FAIL + PARTIAL only, with full detail)
          - all_results array (every control assessed)

        RAG thresholds
        --------------
        GREEN  : pass rate >= 80 %
        AMBER  : pass rate >= 60 %
        RED    : pass rate <  60 %

        Parameters
        ----------
        results : list[AssessmentResult]
            Results from one or more EvidenceAssessor.assess* calls.
        audit_scope : str
            Human-readable description of what was audited, e.g.
            "Vodafone UK — IAM Controls Q1 2026".
        report_id : str, optional
            Override the auto-generated UUID for the report.

        Returns
        -------
        dict
            JSON-serialisable report structure.
        """
        if not report_id:
            report_id = str(uuid.uuid4())

        passed = [r for r in results if r.verdict == Verdict.PASS]
        partial = [r for r in results if r.verdict == Verdict.PARTIAL]
        failed = [r for r in results if r.verdict == Verdict.FAIL]
        insufficient = [r for r in results if r.verdict == Verdict.INSUFFICIENT_EVIDENCE]

        total = len(results)
        pass_rate = round(len(passed) / total * 100, 1) if total else 0.0
        rag = "GREEN" if pass_rate >= 80 else "AMBER" if pass_rate >= 60 else "RED"

        return {
            "report_id": report_id,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "audit_scope": audit_scope,
            "summary": {
                "total_controls_assessed": total,
                "pass": len(passed),
                "partial": len(partial),
                "fail": len(failed),
                "insufficient_evidence": len(insufficient),
                "pass_rate_pct": pass_rate,
                "rag_status": rag,
                "total_tokens_used": sum(r.tokens_used for r in results),
            },
            "findings": [
                r.to_dict()
                for r in results
                if r.verdict in (Verdict.FAIL, Verdict.PARTIAL)
            ],
            "all_results": [r.to_dict() for r in results],
        }

    def save_json_report(
        self,
        results: list[AssessmentResult],
        audit_scope: str,
        output_path: str,
        report_id: Optional[str] = None,
    ) -> str:
        """
        Convenience wrapper: generate the JSON report and write it to disk.

        Parameters
        ----------
        output_path : str
            Destination file path (created including any missing parent dirs).

        Returns
        -------
        str
            The resolved output path.
        """
        report = self.generate_json_report(results, audit_scope, report_id)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return str(path)

    # ------------------------------------------------------------------
    # 2. Rich CLI table
    # ------------------------------------------------------------------

    def generate_summary_table(self, results: list[AssessmentResult]) -> None:
        """
        Print a Rich-formatted assessment results table to stdout.

        Columns
        -------
        Control ID | Control Name | Verdict | Risk | Confidence | Gaps

        A summary footer line with the overall RAG status is printed beneath
        the table.
        """
        console = Console()

        table = Table(
            title="ITGC Evidence Assessment Results",
            box=box.ROUNDED,
            show_lines=True,
            highlight=True,
        )
        table.add_column("Control ID", style="bold cyan", no_wrap=True)
        table.add_column("Control Name", max_width=35)
        table.add_column("Verdict", justify="center", no_wrap=True)
        table.add_column("Risk", justify="center", no_wrap=True)
        table.add_column("Confidence", justify="right", no_wrap=True)
        table.add_column("Gaps", justify="right", no_wrap=True)

        for r in results:
            verdict_text = Text(r.verdict.value, style=VERDICT_COLOUR[r.verdict])
            risk_text = Text(r.risk_rating.value, style=RISK_COLOUR[r.risk_rating])
            table.add_row(
                r.control_id,
                r.control_name,
                verdict_text,
                risk_text,
                f"{r.confidence:.0%}",
                str(r.gap_count),
            )

        console.print(table)

        # Footer with overall RAG status
        passed = sum(1 for r in results if r.verdict == Verdict.PASS)
        total = len(results)
        pass_rate = passed / total * 100 if total else 0.0
        rag_label = (
            "GREEN" if pass_rate >= 80 else "AMBER" if pass_rate >= 60 else "RED"
        )
        rag_colour = (
            "green" if pass_rate >= 80 else "yellow" if pass_rate >= 60 else "red"
        )
        console.print(
            f"\n  Overall RAG Status: "
            f"[bold {rag_colour}]{rag_label}[/bold {rag_colour}]  "
            f"({passed}/{total} controls passed, {pass_rate:.1f}%)\n"
        )

    # ------------------------------------------------------------------
    # 3. PDF report
    # ------------------------------------------------------------------

    def generate_pdf_report(
        self,
        results: list[AssessmentResult],
        audit_scope: str,
        output_path: str,
    ) -> str:
        """
        Generate a professional A4 PDF report using ReportLab.

        Structure
        ---------
        1. Cover section  — title, scope, date, classification
        2. Executive summary table — pass/fail counts and RAG status
        3. Control assessment results table — all controls with colour-coding
        4. Audit findings section (page break) — full narrative per finding

        Parameters
        ----------
        results : list[AssessmentResult]
            Assessment results to include in the report.
        audit_scope : str
            Short description of the audit scope.
        output_path : str
            Destination path for the PDF file (parent dirs created if needed).

        Returns
        -------
        str
            The resolved output path of the written PDF.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()

        # Custom paragraph styles
        title_style = ParagraphStyle(
            "GRCTitle",
            parent=styles["Title"],
            textColor=_VODAFONE_RED,
            fontSize=22,
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "GRCSubtitle",
            parent=styles["Normal"],
            textColor=_DARK_GREY,
            fontSize=11,
            spaceAfter=4,
        )
        h2_style = ParagraphStyle(
            "GRCH2",
            parent=styles["Heading2"],
            textColor=_VODAFONE_RED,
            fontSize=13,
            spaceBefore=12,
            spaceAfter=6,
        )
        h3_style = ParagraphStyle(
            "GRCH3",
            parent=styles["Heading3"],
            textColor=_DARK_GREY,
            fontSize=10,
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "GRCBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            spaceAfter=4,
        )
        confidential_style = ParagraphStyle(
            "GRCConf",
            parent=styles["Normal"],
            textColor=colors.red,
            fontSize=10,
            spaceAfter=4,
        )

        story = []

        # ---------------------------------------------------------------
        # Cover section
        # ---------------------------------------------------------------
        story.append(Spacer(1, 1.5 * cm))
        story.append(Paragraph("ITGC Evidence Assessment Report", title_style))
        story.append(HRFlowable(width="100%", thickness=2, color=_VODAFONE_RED))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"Audit Scope: {audit_scope}", subtitle_style))
        story.append(
            Paragraph(
                f"Generated: {datetime.utcnow().strftime('%d %B %Y %H:%M UTC')}",
                subtitle_style,
            )
        )
        story.append(Paragraph("Classification: CONFIDENTIAL", confidential_style))
        story.append(Spacer(1, 1 * cm))

        # ---------------------------------------------------------------
        # Executive summary
        # ---------------------------------------------------------------
        passed_list = [r for r in results if r.verdict == Verdict.PASS]
        partial_list = [r for r in results if r.verdict == Verdict.PARTIAL]
        failed_list = [r for r in results if r.verdict == Verdict.FAIL]
        insufficient_list = [r for r in results if r.verdict == Verdict.INSUFFICIENT_EVIDENCE]
        total = len(results)
        pass_rate = round(len(passed_list) / total * 100, 1) if total else 0.0
        rag = "GREEN" if pass_rate >= 80 else "AMBER" if pass_rate >= 60 else "RED"
        rag_pdf_colour = {
            "GREEN": colors.HexColor("#155724"),
            "AMBER": colors.HexColor("#856404"),
            "RED": colors.HexColor("#721C24"),
        }[rag]

        story.append(Paragraph("Executive Summary", h2_style))

        summary_data = [
            ["Assessed", "Passed", "Partial", "Failed", "Insufficient", "Pass Rate", "RAG"],
            [
                str(total),
                str(len(passed_list)),
                str(len(partial_list)),
                str(len(failed_list)),
                str(len(insufficient_list)),
                f"{pass_rate}%",
                Paragraph(
                    f'<font color="#{rag_pdf_colour.hexval()[1:]}">'
                    f"<b>{rag}</b></font>",
                    body_style,
                ),
            ],
        ]

        col_w = [2.2 * cm] * 7
        summary_table = RLTable(summary_data, colWidths=col_w)
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _VODAFONE_RED),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_LIGHT_GREY, colors.white]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 0.5 * cm))

        # ---------------------------------------------------------------
        # Control assessment results table
        # ---------------------------------------------------------------
        story.append(Paragraph("Control Assessment Results", h2_style))

        header_row = [
            "Control ID",
            "Control Name",
            "Verdict",
            "Risk Rating",
            "Gaps",
            "Confidence",
        ]
        data_rows = [header_row]
        for r in results:
            data_rows.append(
                [
                    r.control_id,
                    r.control_name[:40],
                    r.verdict.value,
                    r.risk_rating.value,
                    str(r.gap_count),
                    f"{r.confidence:.0%}",
                ]
            )

        results_table = RLTable(
            data_rows,
            colWidths=[2.2 * cm, 5.5 * cm, 2.4 * cm, 2.5 * cm, 1.2 * cm, 2.0 * cm],
        )

        ts = [
            ("BACKGROUND", (0, 0), (-1, 0), _VODAFONE_RED),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        # Apply per-row verdict background colour
        for i, r in enumerate(results, start=1):
            bg = _PDF_VERDICT_BG.get(r.verdict.value, colors.white)
            ts.append(("BACKGROUND", (0, i), (-1, i), bg))

        results_table.setStyle(TableStyle(ts))
        story.append(results_table)

        # ---------------------------------------------------------------
        # Findings detail section
        # ---------------------------------------------------------------
        findings = [r for r in results if r.draft_finding is not None]
        if findings:
            story.append(PageBreak())
            story.append(Paragraph("Audit Findings", h2_style))
            story.append(
                Paragraph(
                    f"The following {len(findings)} finding(s) were identified "
                    "during this assessment. Each finding includes the observation, "
                    "applicable criteria, risk impact, recommended remediation, and "
                    "proposed management action.",
                    body_style,
                )
            )
            story.append(Spacer(1, 0.4 * cm))

            for idx, r in enumerate(findings, start=1):
                f = r.draft_finding

                story.append(
                    Paragraph(
                        f"Finding {idx}: {f.title}",
                        h3_style,
                    )
                )

                # Finding metadata row
                meta_data = [
                    ["Control ID", r.control_id, "Control Name", r.control_name],
                    ["Verdict", r.verdict.value, "Risk Rating", r.risk_rating.value],
                ]
                meta_table = RLTable(
                    meta_data,
                    colWidths=[2.5 * cm, 4.0 * cm, 2.5 * cm, 6.8 * cm],
                )
                meta_table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("BACKGROUND", (0, 0), (-1, -1), _LIGHT_GREY),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ]
                    )
                )
                story.append(meta_table)
                story.append(Spacer(1, 0.2 * cm))

                # Narrative fields
                narrative_items = [
                    ("Observation", f.observation),
                    ("Criteria", f.criteria),
                    ("Risk Impact", f.risk_impact),
                    ("Recommendation", f.recommendation),
                    ("Management Action", f.management_action),
                ]
                for label, value in narrative_items:
                    if value and value.strip():
                        story.append(
                            Paragraph(f"<b>{label}:</b> {value}", body_style)
                        )

                # Remediation notes (from AssessmentResult, not DraftFinding)
                if r.remediation_notes and r.remediation_notes.strip():
                    story.append(
                        Paragraph(
                            f"<b>Detailed Remediation Notes:</b> {r.remediation_notes}",
                            body_style,
                        )
                    )

                # Recommended evidence
                if r.recommended_evidence:
                    story.append(
                        Paragraph("<b>Recommended Additional Evidence:</b>", body_style)
                    )
                    for item in r.recommended_evidence:
                        story.append(Paragraph(f"  - {item}", body_style))

                story.append(
                    HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey)
                )
                story.append(Spacer(1, 0.3 * cm))

        # ---------------------------------------------------------------
        # Footer / build
        # ---------------------------------------------------------------
        doc.build(story)
        return str(path)

    # ------------------------------------------------------------------
    # Helper: RAG string from a list of results
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_rag(results: list[AssessmentResult]) -> tuple[float, str]:
        """Return (pass_rate_pct, rag_label) for a list of results."""
        total = len(results)
        if not total:
            return 0.0, "RED"
        passed = sum(1 for r in results if r.verdict == Verdict.PASS)
        rate = round(passed / total * 100, 1)
        label = "GREEN" if rate >= 80 else "AMBER" if rate >= 60 else "RED"
        return rate, label

    # ------------------------------------------------------------------
    # Single-assessment PDF generator
    # ------------------------------------------------------------------

    def generate_single_pdf(
        self,
        result: dict,
        output_path: str,
    ) -> str:
        """
        Generate a detailed single-assessment PDF report with professional
        audit formatting — callout boxes, colour-coded tables, row striping,
        page numbers, and proper text wrapping throughout.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # ---- Page number canvas ----
        def _add_page_number(canvas_obj, doc):
            canvas_obj.saveState()
            canvas_obj.setFont("Helvetica", 7)
            canvas_obj.setFillColor(colors.grey)
            canvas_obj.drawRightString(
                A4[0] - 2 * cm, 1.5 * cm,
                f"Page {canvas_obj.getPageNumber()}"
            )
            canvas_obj.drawString(
                2 * cm, 1.5 * cm,
                "ITGC Evidence Analyser — Vodafone GRC  |  CONFIDENTIAL"
            )
            canvas_obj.restoreState()

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
        )

        styles = getSampleStyleSheet()
        page_w = A4[0] - 4 * cm  # usable width

        # ---- Paragraph styles ----
        title_style = ParagraphStyle(
            "RptTitle", parent=styles["Title"],
            textColor=_VODAFONE_RED, fontSize=22, leading=26, spaceAfter=4,
        )
        h2_style = ParagraphStyle(
            "RptH2", parent=styles["Heading2"],
            textColor=_VODAFONE_RED, fontSize=12, leading=15,
            spaceBefore=18, spaceAfter=8,
        )
        body = ParagraphStyle(
            "RptBody", parent=styles["Normal"],
            fontSize=9, leading=14, spaceAfter=5,
        )
        body_small = ParagraphStyle(
            "RptBodySm", parent=body, fontSize=8, leading=12, spaceAfter=2,
        )
        cell_style = ParagraphStyle(
            "RptCell", parent=body, fontSize=8, leading=11, spaceAfter=0,
        )
        cell_bold = ParagraphStyle(
            "RptCellBold", parent=cell_style, fontName="Helvetica-Bold",
        )
        header_cell = ParagraphStyle(
            "RptHdr", parent=cell_style, fontName="Helvetica-Bold",
            textColor=colors.white, fontSize=7.5, leading=10,
        )
        label_cell = ParagraphStyle(
            "RptLabel", parent=cell_style, fontName="Helvetica-Bold",
            fontSize=8, leading=12, textColor=_DARK_GREY,
        )
        callout_body = ParagraphStyle(
            "CalloutBody", parent=body, fontSize=9, leading=14,
        )
        meta_style = ParagraphStyle(
            "RptMeta", parent=styles["Normal"],
            fontSize=8, leading=11, textColor=colors.grey, spaceAfter=3,
        )

        story = []

        # ---- COVER / HEADER ----
        story.append(Spacer(1, 0.8 * cm))
        story.append(HRFlowable(width="30%", thickness=3, color=_VODAFONE_RED, spaceAfter=8))
        story.append(Paragraph("ITGC Evidence<br/>Assessment Report", title_style))
        story.append(Spacer(1, 0.4 * cm))

        control_name = result.get("control_name", result.get("control_id", "Unknown"))
        cid = result.get("control_id", "—")
        stype = result.get("statement_type", "—")
        assessed = result.get("assessed_at", "—")
        if assessed and len(assessed) >= 19:
            assessed = assessed[:19]
        model = result.get("model_used", "—")

        market_name = result.get("market_name", "")
        samples = result.get("samples", [])

        meta_rows = [
            [
                Paragraph(f"<b>Control</b><br/>{cid} — {control_name}", cell_style),
                Paragraph(f"<b>Type</b><br/>{'Design' if stype == 'D' else 'Evidence'} Assessment", cell_style),
                Paragraph(f"<b>Assessed</b><br/>{assessed}", cell_style),
                Paragraph(f"<b>Model</b><br/>{model}", cell_style),
            ]
        ]
        if market_name or (isinstance(samples, list) and samples):
            second_row = []
            if market_name:
                second_row.append(Paragraph(f"<b>Market</b><br/>{market_name}", cell_style))
            else:
                second_row.append(Paragraph("", cell_style))
            if isinstance(samples, list) and samples:
                samples_text = ", ".join(samples)
                second_row.append(Paragraph(f"<b>Samples in Scope</b><br/>{samples_text}", cell_style))
            if len(second_row) == 1:
                second_row.append(Paragraph("", cell_style))
            if len(second_row) == 2:
                second_row.append(Paragraph("", cell_style))
                second_row.append(Paragraph("", cell_style))
            meta_rows.append(second_row)

        meta_table = RLTable(meta_rows, colWidths=[6.5 * cm, 3.2 * cm, 3.2 * cm, 2.9 * cm])
        meta_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 0.5 * cm))

        # ---- VERDICT SUMMARY PANEL ----
        verdict = result.get("verdict", "INSUFFICIENT_EVIDENCE")
        verdict_bg = _PDF_VERDICT_BG.get(verdict, colors.HexColor("#E2E3E5"))
        verdict_hex_fg = {
            "PASS": "155724",
            "PARTIAL": "856404",
            "FAIL": "721C24",
            "INSUFFICIENT_EVIDENCE": "383D41",
        }
        verdict_hex = verdict_hex_fg.get(verdict, "333333")

        risk = result.get("risk_rating", "—")
        conf = result.get("confidence", 0)
        conf_str = f"{conf:.0%}" if isinstance(conf, (int, float)) else str(conf)
        compliance = result.get("compliance_status", "—")

        panel_data = [[
            Paragraph(
                f"<font size='9' color='#{verdict_hex}'>VERDICT</font><br/>"
                f"<font size='16'><b>{verdict}</b></font>",
                ParagraphStyle("V1", parent=cell_style, alignment=1, leading=16),
            ),
            Paragraph(
                f"<font size='9' color='#666666'>CONFIDENCE</font><br/>"
                f"<font size='16'><b>{conf_str}</b></font>",
                ParagraphStyle("V2", parent=cell_style, alignment=1, leading=16),
            ),
            Paragraph(
                f"<font size='9' color='#666666'>RISK RATING</font><br/>"
                f"<font size='14'><b>{risk}</b></font>",
                ParagraphStyle("V3", parent=cell_style, alignment=1, leading=16),
            ),
            Paragraph(
                f"<font size='9' color='#666666'>COMPLIANCE</font><br/>"
                f"<font size='14'><b>{compliance}</b></font>",
                ParagraphStyle("V4", parent=cell_style, alignment=1, leading=16),
            ),
        ]]
        panel = RLTable(panel_data, colWidths=[
            3.8 * cm, 3.2 * cm, 3.8 * cm, 5 * cm,
        ])
        panel.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), verdict_bg),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBEFORE", (1, 0), (3, 0), 0.5, colors.white),
            ("LINEBEFORE", (0, 0), (0, 0), 0, colors.white),
            ("LINEAFTER", (-1, 0), (-1, 0), 0, colors.white),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ]))
        story.append(panel)
        story.append(Spacer(1, 0.6 * cm))

        # ---- AUDIT OPINION ----
        opinion = result.get("audit_opinion", "")
        if opinion:
            story.append(Paragraph("Audit Opinion", h2_style))
            # Callout box
            op_data = [[Paragraph(opinion, callout_body)]]
            op_table = RLTable(op_data, colWidths=[page_w])
            op_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LINEBEFORE", (0, 0), (0, 0), 3, _VODAFONE_RED),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ]))
            story.append(op_table)
            story.append(Spacer(1, 0.4 * cm))

        # ---- METHODOLOGY + COMPLIANCE ----
        meth = result.get("assessment_methodology", "")
        if compliance or meth:
            story.append(Paragraph("Assessment Details", h2_style))
            detail_rows = []
            if compliance:
                detail_rows.append([
                    Paragraph("Compliance Status", label_cell),
                    Paragraph(compliance, cell_style),
                ])
            if meth:
                detail_rows.append([
                    Paragraph("Methodology", label_cell),
                    Paragraph(meth, cell_style),
                ])
            detail_table = RLTable(detail_rows, colWidths=[3.8 * cm, 12 * cm])
            detail_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), _LIGHT_GREY),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(detail_table)
            story.append(Spacer(1, 0.4 * cm))

        # ---- DRAFT FINDING ----
        finding = result.get("draft_finding")
        if finding and isinstance(finding, dict):
            story.append(PageBreak())
            story.append(Paragraph("Audit Finding", h2_style))
            finding_data = [
                [Paragraph("Title", label_cell),
                 Paragraph(finding.get("title", "—"), ParagraphStyle(
                     "FTitle", parent=cell_style, fontName="Helvetica-Bold", fontSize=9, leading=13,
                 ))],
                [Paragraph("Observation", label_cell),
                 Paragraph(finding.get("observation", "—"), cell_style)],
                [Paragraph("Criteria", label_cell),
                 Paragraph(finding.get("criteria", "—"), cell_style)],
                [Paragraph("Risk &amp; Impact", label_cell),
                 Paragraph(finding.get("risk_impact", "—"), cell_style)],
                [Paragraph("Recommendation", label_cell),
                 Paragraph(finding.get("recommendation", "—"), cell_style)],
                [Paragraph("Management Action", label_cell),
                 Paragraph(finding.get("management_action", "—"), cell_style)],
            ]
            finding_table = RLTable(finding_data, colWidths=[3.8 * cm, 12 * cm])
            finding_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#FFF3CD")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E6D8A7")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#F5A623")),
            ]))
            story.append(finding_table)
            story.append(Spacer(1, 0.3 * cm))

        # ---- JUSTIFICATION ----
        justification = result.get("justification", "")
        if justification:
            story.append(Paragraph("Justification", h2_style))
            story.append(Paragraph(justification, body))
            story.append(Spacer(1, 0.3 * cm))

        # ---- REQUIREMENTS ASSESSMENT ----
        satisfied = result.get("satisfied_requirements") or []
        gaps = result.get("gaps") or []
        if satisfied or gaps:
            story.append(PageBreak())
            story.append(Paragraph("Requirements Assessment", h2_style))
            status_header = Paragraph("Status", header_cell)
            detail_header = Paragraph("Detail", header_cell)
            req_data = [[status_header, detail_header]]
            for s in satisfied:
                req_data.append([
                    Paragraph("<font color='#155724'><b>SATISFIED</b></font>", cell_bold),
                    Paragraph(s, cell_style),
                ])
            for g in gaps:
                req_data.append([
                    Paragraph("<font color='#721C24'><b>GAP</b></font>", cell_bold),
                    Paragraph(g, cell_style),
                ])
            req_table = RLTable(req_data, colWidths=[3.5 * cm, 12.3 * cm])
            ts = [
                ("BACKGROUND", (0, 0), (-1, 0), _VODAFONE_RED),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
            # Row striping
            for i in range(1, len(req_data)):
                if i % 2 == 0:
                    ts.append(("BACKGROUND", (0, i), (-1, i), _LIGHT_GREY))
            req_table.setStyle(TableStyle(ts))
            story.append(req_table)
            story.append(Spacer(1, 0.3 * cm))

        # ---- STATEMENT-BY-STATEMENT TABLE ----
        req_assess = result.get("requirement_assessment") or []
        if req_assess and len(req_assess) > 0:
            story.append(Paragraph("Statement-by-Statement Assessment", h2_style))
            ra_data = [[
                Paragraph("ID", header_cell),
                Paragraph("Status", header_cell),
                Paragraph("Evidence Ref", header_cell),
                Paragraph("Assessment Detail", header_cell),
            ]]
            for ra in req_assess:
                status = ra.get("status", "—")
                status_colour = {
                    "MET": "#155724", "PARTIALLY_MET": "#856404",
                    "NOT_MET": "#721C24",
                }.get(status, "#333333")
                ra_data.append([
                    Paragraph(ra.get("statement_id", "—"), cell_bold),
                    Paragraph(f"<font color='{status_colour}'><b>{status}</b></font>", cell_style),
                    Paragraph(ra.get("evidence_ref", "—"), cell_style),
                    Paragraph(ra.get("assessment_detail", "—"), cell_style),
                ])
            ra_table = RLTable(ra_data, colWidths=[2 * cm, 2.8 * cm, 3 * cm, 8 * cm])
            ts = [
                ("BACKGROUND", (0, 0), (-1, 0), _VODAFONE_RED),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
            for i in range(1, len(ra_data)):
                if i % 2 == 0:
                    ts.append(("BACKGROUND", (0, i), (-1, i), _LIGHT_GREY))
            ra_table.setStyle(TableStyle(ts))
            story.append(ra_table)
            story.append(Spacer(1, 0.3 * cm))

        # ---- EVIDENCE INVENTORY ----
        evidence = result.get("evidence_inventory") or []
        if evidence and len(evidence) > 0:
            story.append(PageBreak())
            story.append(Paragraph("Evidence Inventory", h2_style))
            ev_data = [[
                Paragraph("File / Description", header_cell),
                Paragraph("Type", header_cell),
                Paragraph("Date", header_cell),
                Paragraph("Strength", header_cell),
                Paragraph("Notes", header_cell),
            ]]
            for ei in evidence:
                strength = ei.get("strength_rating", "—")
                strength_colour = {
                    "STRONG": "#155724", "MODERATE": "#856404",
                    "WEAK": "#721C24", "NIL": "#999999",
                }.get(strength, "#333333")
                ev_data.append([
                    Paragraph(ei.get("file", "—"), cell_style),
                    Paragraph(ei.get("type", "—"), cell_style),
                    Paragraph(ei.get("date_observed") or "—", cell_style),
                    Paragraph(f"<font color='{strength_colour}'><b>{strength}</b></font>", cell_style),
                    Paragraph(ei.get("notes", "—"), cell_style),
                ])
            ev_table = RLTable(ev_data, colWidths=[4 * cm, 2.2 * cm, 2.4 * cm, 2.2 * cm, 5 * cm])
            ts = [
                ("BACKGROUND", (0, 0), (-1, 0), _VODAFONE_RED),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
            for i in range(1, len(ev_data)):
                if i % 2 == 0:
                    ts.append(("BACKGROUND", (0, i), (-1, i), _LIGHT_GREY))
            ev_table.setStyle(TableStyle(ts))
            story.append(ev_table)
            story.append(Spacer(1, 0.3 * cm))

        # ---- LIMITATIONS ----
        limitations = result.get("limitations") or []
        if limitations and len(limitations) > 0:
            story.append(Paragraph("Limitations", h2_style))
            for lim in limitations:
                story.append(Paragraph(f"<bullet>&bull;</bullet> {lim}", body_small))
            story.append(Spacer(1, 0.3 * cm))

        # ---- FOLLOW-UP QUESTIONS ----
        questions = result.get("follow_up_questions") or []
        if questions and len(questions) > 0:
            story.append(Paragraph("Follow-up Questions", h2_style))
            for i, q in enumerate(questions, 1):
                story.append(Paragraph(f"<b>{i}.</b> {q}", body))
            story.append(Spacer(1, 0.3 * cm))

        # ---- RECOMMENDED EVIDENCE ----
        rec_evidence = result.get("recommended_evidence") or []
        if rec_evidence and len(rec_evidence) > 0:
            story.append(Paragraph("Recommended Additional Evidence", h2_style))
            for item in rec_evidence:
                story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", body_small))
            story.append(Spacer(1, 0.3 * cm))

        # ---- REMEDIATION ----
        remediation = result.get("remediation_notes", "")
        if remediation:
            story.append(Paragraph("Remediation Guidance", h2_style))
            rem_data = [[Paragraph(remediation, callout_body)]]
            rem_table = RLTable(rem_data, colWidths=[page_w])
            rem_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8F5E9")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LINEBEFORE", (0, 0), (0, 0), 3, colors.HexColor("#22C55E")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C8E6C9")),
            ]))
            story.append(rem_table)
            story.append(Spacer(1, 0.3 * cm))

        # ---- FOOTER DIVIDER ----
        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DEE2E6")))
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            f"Generated: {datetime.utcnow().strftime('%d %B %Y %H:%M UTC')}  |  "
            f"Model: {result.get('model_used', '—')}  |  "
            f"Tokens: {result.get('tokens_used', 0):,}",
            ParagraphStyle("Footer", parent=meta_style),
        ))

        doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
        return str(path)
