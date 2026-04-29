"""Output generators — terminal, JSON, Markdown, and PDF reports."""

import json
import re
from pathlib import Path

from .models import VendorAssessment, RiskRating, Answer


RISK_COLORS = {
    RiskRating.LOW: "\033[92m",       # green
    RiskRating.MEDIUM: "\033[93m",    # yellow
    RiskRating.HIGH: "\033[91m",      # red (bright)
    RiskRating.CRITICAL: "\033[91m",  # red
}
RESET = "\033[0m"
BOLD = "\033[1m"


def print_assessment(assessment: VendorAssessment) -> None:
    """Print a formatted terminal assessment."""
    color = RISK_COLORS.get(assessment.risk_rating, "")
    total_questions = len(assessment.questions)
    scored_questions = sum(1 for q in assessment.questions if q.is_scored())
    na_count = total_questions - scored_questions

    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  VENDOR SECURITY ASSESSMENT{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    print(f"  Vendor:        {assessment.vendor_name}")
    print(f"  Date:          {assessment.assessment_date}")
    print(f"  Questions:     {total_questions} total ({scored_questions} scored, {na_count} N/A)")
    print(f"  Overall Score: {color}{assessment.overall_score:.1f}%{RESET}")
    print(f"  Risk Rating:   {color}{BOLD}{assessment.risk_rating.value}{RESET}")
    print(f"{'='*70}")

    print(f"\n{BOLD}  CATEGORY BREAKDOWN{RESET}")
    print(f"  {'Category':<22} {'Score':>7}  {'Max':>7}  {'Pct':>7}  Rating")
    print(f"  {'-'*22} {'-'*7}  {'-'*7}  {'-'*7}  {'-'*10}")
    for cs in assessment.category_scores:
        c = RISK_COLORS.get(cs.risk_level, "")
        print(f"  {cs.category:<22} {cs.total_weighted:>7.1f}  {cs.max_possible:>7.1f}  {cs.pct:>6.1f}%  {c}{cs.risk_level.value:<10}{RESET}")

    if assessment.top_risks:
        print(f"\n{BOLD}  TOP RISKS ({len(assessment.top_risks)}){RESET}")
        for risk in assessment.top_risks:
            print(f"    {RISK_COLORS[RiskRating.HIGH]}[!]{RESET} {risk}")

    if assessment.remediation_checklist:
        print(f"\n{BOLD}  REMEDIATION CHECKLIST{RESET}")
        print(f"  ({len(assessment.remediation_checklist)} total items — showing first 5)")
        for item in assessment.remediation_checklist[:5]:
            print(f"    - {item}")
        if len(assessment.remediation_checklist) > 5:
            print(f"    ... and {len(assessment.remediation_checklist) - 5} more items.")

    print(f"\n{BOLD}{'='*70}{RESET}\n")


def save_report_json(assessment: VendorAssessment, path: str) -> str:
    """Save the full assessment as a JSON file."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = assessment.to_dict()
    out.write_text(json.dumps(data, indent=2, default=str))
    return str(out)


def save_report_md(assessment: VendorAssessment, path: str) -> str:
    """Save the assessment as a Markdown report."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# Vendor Security Assessment: {assessment.vendor_name}")
    lines.append("")
    lines.append(f"**Date:** {assessment.assessment_date}  ")
    lines.append(f"**Overall Score:** {assessment.overall_score:.1f}%  ")
    lines.append(f"**Risk Rating:** **{assessment.risk_rating.value}**  ")
    lines.append("")

    total = len(assessment.questions)
    scored = sum(1 for q in assessment.questions if q.is_scored())
    lines.append(f"*{total} questions ({scored} scored, {total - scored} N/A)*")
    lines.append("")

    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | Score | Max | Pct | Rating |")
    lines.append("|----------|------:|----:|----:|--------|")
    for cs in assessment.category_scores:
        lines.append(f"| {cs.category} | {cs.total_weighted:.1f} | {cs.max_possible:.1f} | {cs.pct:.1f}% | {cs.risk_level.value} |")
    lines.append("")

    if assessment.top_risks:
        lines.append("## Top Risks")
        lines.append("")
        for risk in assessment.top_risks:
            lines.append(f"- {risk}")
        lines.append("")

    if assessment.remediation_checklist:
        lines.append("## Remediation Checklist")
        lines.append("")
        for item in assessment.remediation_checklist:
            lines.append(f"- {item}")
        lines.append("")

    out.write_text("\n".join(lines))
    return str(out)


# ── PDF helpers ────────────────────────────────────────────────


def _p(text, style):
    """Wrap text in a ReportLab Paragraph so it word-wraps inside table cells."""
    from reportlab.platypus import Paragraph

    return Paragraph(str(text), style)


def _hdr_row(labels, style):
    """Build a header row of bold Paragraph cells."""
    return [_p(l, style) for l in labels]


def _parse_top_risk(item: str) -> tuple[str, str]:
    """Parse a top-risk string '[Category] Question text' into (category, question)."""
    m = re.match(r"^\[(.+?)\]\s+(.+)$", item)
    if m:
        return m.group(1), m.group(2)
    return "", item


def _parse_remediation(item: str) -> tuple[str, str, str, str]:
    """Parse a remediation string into (category, question, answer, action)."""
    m = re.match(
        r"^\[(.+?)\]\s+(.+?)\s+—\s+Vendor response was (NO|PARTIAL)\.\s+(.+)$",
        item,
    )
    if m:
        return m.group(1), m.group(2), m.group(3), m.group(4)
    return "", item, "", item


def export_pdf(assessment: VendorAssessment, output_path: str) -> str:
    """Generate a professional PDF vendor assessment report using ReportLab.

    All table cells use Paragraph objects so text wraps correctly within
    column boundaries. Follows P5 reporter.py conventions.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.colors import HexColor
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
            HRFlowable,
            Flowable,
        )
    except ImportError:
        raise ImportError(
            "reportlab required for PDF output. Install with: pip install reportlab"
        )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # ── Page template with footer ───────────────────────────────
    def _on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor("#999999"))
        footer_text = (
            "Vendor Security Questionnaire Scorer — GRC Portfolio | CONFIDENTIAL"
        )
        canvas.drawString(1.5 * cm, 1 * cm, footer_text)
        canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=f"Vendor Security Assessment — {assessment.vendor_name}",
        author="Vendor Security Questionnaire Scorer",
    )

    styles = getSampleStyleSheet()

    # ── Brand colours ──────────────────────────────────────────
    VODAFONE_RED = HexColor("#E60000")
    RAG_GREEN_BG = HexColor("#D4EDDA")
    RAG_AMBER_BG = HexColor("#FFF3CD")
    RAG_RED_BG = HexColor("#F8D7DA")
    NA_GREY_BG = HexColor("#E9ECEF")
    HEADER_BG = VODAFONE_RED
    LABEL_BG = HexColor("#F5F5F5")
    ROW_A = HexColor("#FFFFFF")
    ROW_B = HexColor("#FAFAFA")
    BORDER = HexColor("#CCCCCC")
    GREEN_BAR = HexColor("#28A745")
    AMBER_BAR = HexColor("#FFC107")
    RED_BAR = HexColor("#DC3545")

    # ── Shared cell styles ─────────────────────────────────────
    cell_body = ParagraphStyle(
        "VendorCellBody",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=10,
        wordWrap="CJK",
    )
    cell_bold = ParagraphStyle(
        "VendorCellBold",
        parent=cell_body,
        fontName="Helvetica-Bold",
    )
    cell_hdr = ParagraphStyle(
        "VendorCellHdr",
        parent=cell_body,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=HexColor("#FFFFFF"),
    )
    cell_sm = ParagraphStyle(
        "VendorCellSm",
        parent=cell_body,
        fontSize=7,
        leading=9,
        wordWrap="CJK",
    )

    # ── Risk-rating colour helpers ─────────────────────────────
    def _risk_bg(rating: RiskRating):
        if rating in (RiskRating.HIGH, RiskRating.CRITICAL):
            return RAG_RED_BG
        elif rating == RiskRating.MEDIUM:
            return RAG_AMBER_BG
        else:
            return RAG_GREEN_BG

    def _risk_fg(rating: RiskRating):
        if rating in (RiskRating.HIGH, RiskRating.CRITICAL):
            return HexColor("#721C24")
        elif rating == RiskRating.MEDIUM:
            return HexColor("#856404")
        else:
            return HexColor("#155724")

    def _answer_bg(ans: str) -> HexColor:
        return {
            "YES": RAG_GREEN_BG,
            "PARTIAL": RAG_AMBER_BG,
            "NO": RAG_RED_BG,
            "NA": NA_GREY_BG,
        }.get(ans, HexColor("#FFFFFF"))

    # ── Bar Flowable for percentage bar column ─────────────────
    class _BarFlowable(Flowable):
        """A horizontal bar showing a percentage."""

        def __init__(self, pct_val, width, height=8):
            Flowable.__init__(self)
            self.pct_val = max(0.0, min(100.0, float(pct_val)))
            self._width = width
            self._height = height

        def wrap(self, availWidth, availHeight):
            return (self._width, self._height)

        def draw(self):
            # Background track
            self.canv.setFillColor(NA_GREY_BG)
            self.canv.rect(0, 0, self._width, self._height, fill=1, stroke=0)
            # Filled portion
            if self.pct_val >= 70:
                colour = GREEN_BAR
            elif self.pct_val >= 50:
                colour = AMBER_BAR
            else:
                colour = RED_BAR
            self.canv.setFillColor(colour)
            self.canv.rect(
                0,
                0,
                self._width * self.pct_val / 100.0,
                self._height,
                fill=1,
                stroke=0,
            )

    story = []

    total_q = len(assessment.questions)
    scored_q = sum(1 for q in assessment.questions if q.is_scored())
    na_q = total_q - scored_q

    # ══════════════════════════════════════════════════════════════
    #  1. COVER / TITLE SECTION
    # ══════════════════════════════════════════════════════════════

    story.append(
        Paragraph(
            "Vendor Security Assessment Report",
            ParagraphStyle(
                "VendorTitle",
                parent=styles["Title"],
                fontSize=20,
                leading=24,
                textColor=VODAFONE_RED,
                spaceAfter=4,
            ),
        )
    )
    story.append(HRFlowable(width="100%", color=VODAFONE_RED, thickness=1.5))
    story.append(Spacer(1, 0.6 * cm))

    # Vendor info box
    info_rows = [
        [_p("Vendor", cell_bold), _p(assessment.vendor_name, cell_body)],
        [
            _p("Assessment Date", cell_bold),
            _p(assessment.assessment_date, cell_body),
        ],
        [
            _p("Total Questions", cell_bold),
            _p(f"{total_q} ({scored_q} scored, {na_q} N/A)", cell_body),
        ],
    ]
    info_table = Table(info_rows, colWidths=[4 * cm, 14 * cm])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LABEL_BG),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 0.8 * cm))

    # Overall Score card — large bordered box, coloured by risk level
    score_text = f"{assessment.overall_score:.1f}%"
    rating_text = assessment.risk_rating.value
    rating_bg = _risk_bg(assessment.risk_rating)
    rating_fg = _risk_fg(assessment.risk_rating)

    score_card_data = [
        [
            _p(
                f"<b>Overall Score</b><br/>"
                f"<font size='28'><b>{score_text}</b></font><br/>"
                f"<font size='14' color='{rating_fg}'><b>{rating_text}</b></font>",
                ParagraphStyle(
                    "ScoreCard",
                    parent=cell_body,
                    fontSize=10,
                    leading=14,
                    alignment=TA_CENTER,
                ),
            )
        ]
    ]
    score_card = Table(score_card_data, colWidths=[10 * cm])
    score_card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), rating_bg),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("BOX", (0, 0), (-1, -1), 1.5, VODAFONE_RED),
            ]
        )
    )
    story.append(score_card)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    #  2. CATEGORY BREAKDOWN TABLE
    # ══════════════════════════════════════════════════════════════

    story.append(
        Paragraph(
            "Category Breakdown",
            ParagraphStyle(
                "VendorH2",
                parent=styles["Heading2"],
                fontSize=13,
                leading=16,
                spaceBefore=6,
                spaceAfter=8,
                textColor=HexColor("#333333"),
            ),
        )
    )

    cat_rows = [
        _hdr_row(
            ["Category", "Score", "Max", "Pct", "Risk Rating", "Coverage"],
            cell_hdr,
        )
    ]
    for cs in assessment.category_scores:
        cs_bg = _risk_bg(cs.risk_level)
        cs_fg = _risk_fg(cs.risk_level)
        cat_rows.append(
            [
                _p(cs.category, cell_bold),
                _p(f"{cs.total_weighted:.1f}", cell_body),
                _p(f"{cs.max_possible:.1f}", cell_body),
                _p(f"{cs.pct:.1f}%", cell_body),
                _p(
                    f'<font color="{cs_fg}"><b>{cs.risk_level.value}</b></font>',
                    cell_body,
                ),
                _BarFlowable(cs.pct, 5 * cm),
            ]
        )

    cat_table = Table(
        cat_rows,
        colWidths=[3.5 * cm, 2 * cm, 2 * cm, 2 * cm, 2.5 * cm, 5 * cm],
    )
    cat_style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
        ("ALIGN", (1, 0), (3, -1), "CENTER"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
    ]
    # Colour the Risk Rating cells
    for i, cs in enumerate(assessment.category_scores, 1):
        cat_style_cmds.append(("BACKGROUND", (4, i), (4, i), _risk_bg(cs.risk_level)))
    cat_table.setStyle(TableStyle(cat_style_cmds))
    story.append(cat_table)
    story.append(Spacer(1, 0.4 * cm))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    #  3. TOP RISKS SECTION
    # ══════════════════════════════════════════════════════════════

    story.append(
        Paragraph(
            "Top Risks",
            ParagraphStyle(
                "VendorH2b",
                parent=styles["Heading2"],
                fontSize=13,
                leading=16,
                spaceBefore=6,
                spaceAfter=8,
                textColor=VODAFONE_RED,
            ),
        )
    )

    if assessment.top_risks:
        tr_rows = [_hdr_row(["#", "Category", "Question"], cell_hdr)]
        for i, risk_str in enumerate(assessment.top_risks, 1):
            cat, qtext = _parse_top_risk(risk_str)
            tr_rows.append(
                [
                    _p(str(i), cell_bold),
                    _p(
                        f'<font color="#E60000"><b>{cat}</b></font>',
                        cell_body,
                    ),
                    _p(qtext, cell_body),
                ]
            )
        tr_table = Table(
            tr_rows, colWidths=[1 * cm, 3.5 * cm, 13.5 * cm]
        )
        tr_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ]
            )
        )
        story.append(tr_table)
    else:
        story.append(
            _p("<i>No top risks identified.</i>", cell_body)
        )

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    #  4. REMEDIATION CHECKLIST
    # ══════════════════════════════════════════════════════════════

    story.append(
        Paragraph(
            "Remediation Checklist",
            ParagraphStyle(
                "VendorH2c",
                parent=styles["Heading2"],
                fontSize=13,
                leading=16,
                spaceBefore=6,
                spaceAfter=8,
                textColor=HexColor("#333333"),
            ),
        )
    )

    if assessment.remediation_checklist:
        rc_rows = [
            _hdr_row(
                ["#", "Category", "Question", "Answer", "Remediation Action"],
                cell_hdr,
            )
        ]
        for i, item in enumerate(assessment.remediation_checklist, 1):
            cat, qtext, ans, action = _parse_remediation(item)
            ans_bg = {
                "NO": RAG_RED_BG,
                "PARTIAL": RAG_AMBER_BG,
            }.get(ans, HexColor("#FFFFFF"))
            rc_rows.append(
                [
                    _p(str(i), cell_sm),
                    _p(cat, cell_sm),
                    _p(qtext, cell_sm),
                    _p(f"<b>{ans}</b>", cell_sm),
                    _p(action, cell_sm),
                ]
            )
        rc_table = Table(
            rc_rows,
            colWidths=[1 * cm, 2.8 * cm, 5.5 * cm, 2 * cm, 6.7 * cm],
        )
        rc_style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ]
        # Colour NO rows with light red, PARTIAL rows with light amber
        for i, item in enumerate(assessment.remediation_checklist, 1):
            _, _, ans, _ = _parse_remediation(item)
            if ans == "NO":
                rc_style_cmds.append(
                    ("BACKGROUND", (3, i), (3, i), RAG_RED_BG)
                )
            elif ans == "PARTIAL":
                rc_style_cmds.append(
                    ("BACKGROUND", (3, i), (3, i), RAG_AMBER_BG)
                )
        rc_table.setStyle(TableStyle(rc_style_cmds))
        story.append(rc_table)
    else:
        story.append(
            _p("<i>No remediation items. All questions passed.</i>", cell_body)
        )

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    #  5. FULL QUESTION APPENDIX
    # ══════════════════════════════════════════════════════════════

    story.append(
        Paragraph(
            "Full Question Appendix",
            ParagraphStyle(
                "VendorH2d",
                parent=styles["Heading2"],
                fontSize=13,
                leading=16,
                spaceBefore=6,
                spaceAfter=8,
                textColor=HexColor("#333333"),
            ),
        )
    )

    fq_rows = [
        _hdr_row(
            ["#", "Category", "Question", "Weight", "Answer"],
            cell_hdr,
        )
    ]
    for i, q in enumerate(assessment.questions, 1):
        abg = _answer_bg(q.answer.value)
        fq_rows.append(
            [
                _p(str(i), cell_sm),
                _p(q.category, cell_sm),
                _p(q.text, cell_sm),
                _p(q.weight.value, cell_sm),
                _p(f"<b>{q.answer.value}</b>", cell_sm),
            ]
        )

    fq_table = Table(
        fq_rows,
        colWidths=[1 * cm, 2.8 * cm, 8.2 * cm, 2 * cm, 4 * cm],
    )
    fq_style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_A, ROW_B]),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (4, -1), "CENTER"),
    ]
    # Colour answer cells
    for i, q in enumerate(assessment.questions, 1):
        fq_style_cmds.append(
            ("BACKGROUND", (4, i), (4, i), _answer_bg(q.answer.value))
        )
    fq_table.setStyle(TableStyle(fq_style_cmds))
    story.append(fq_table)

    # ── End-of-report marker ────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", color=HexColor("#CCCCCC"), thickness=0.5))
    story.append(
        Paragraph(
            f"Vendor Security Questionnaire Scorer — GRC Portfolio | "
            f"Assessment Date: {assessment.assessment_date} | "
            f"Vendor: {assessment.vendor_name}",
            ParagraphStyle(
                "VendorFooterNote",
                parent=styles["Normal"],
                fontSize=7,
                textColor=HexColor("#999999"),
                leading=9,
            ),
        )
    )

    # ── Build ───────────────────────────────────────────────────
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return str(out)
