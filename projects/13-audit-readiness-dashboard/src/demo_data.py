"""Built-in demo data reflecting all 12 GRC portfolio projects."""

from datetime import date, datetime, timedelta

from src.models import (
    ProjectInfo,
    ProjectType,
    ProjectStatus,
    RAG,
    ControlCoverage,
    CoverageStatus,
    Deadline,
    SummaryStats,
    DashboardData,
)

# Alias for the lifecycle enum
PS = ProjectStatus


TODAY = date.today()


def _d(offset_days: int) -> str:
    """Return ISO date string offset from today."""
    return (TODAY + timedelta(days=offset_days)).isoformat()


def _past(offset_days: int) -> str:
    """Return ISO date string in the past."""
    return (TODAY - timedelta(days=offset_days)).isoformat()


def get_projects() -> list[ProjectStatus]:
    return [
        ProjectInfo(
            project_id="P1",
            name="ITGC Evidence Analyser",
            type=ProjectType.WEB,
            status=PS.COMPLETE,
            test_count=80,
            last_audit_date=_past(7),
            controls_covered=["IAM", "Audit & Assurance"],
            evidence_freshness_days=7,
            rag=RAG.GREEN,
            description="AI-powered CLI and REST API for ITGC audit evidence assessment using Claude AI.",
            port=8001,
        ),
        ProjectInfo(
            project_id="P2",
            name="Evidence Collection Automation",
            type=ProjectType.WEB,
            status=PS.COMPLETE,
            test_count=106,
            last_audit_date=_past(14),
            controls_covered=["IAM", "Audit & Assurance", "SIEM & Monitoring"],
            evidence_freshness_days=14,
            rag=RAG.GREEN,
            description="Automated evidence collection from 7 enterprise systems + IAM lifecycle simulator.",
            port=8002,
        ),
        ProjectInfo(
            project_id="P3",
            name="Vuln SLA Tracker",
            type=ProjectType.WEB,
            status=PS.COMPLETE,
            test_count=70,
            last_audit_date=_past(3),
            controls_covered=["Vulnerability Management", "SIEM & Monitoring"],
            evidence_freshness_days=3,
            rag=RAG.GREEN,
            description="Scanner ingestion, SLA breach engine, and Plotly dashboards for vulnerability tracking.",
            port=8003,
        ),
        ProjectInfo(
            project_id="P4",
            name="DevSecOps Evidence Collector",
            type=ProjectType.CLI,
            status=PS.COMPLETE,
            test_count=79,
            last_audit_date=_past(21),
            controls_covered=["DevSecOps", "Endpoint Security"],
            evidence_freshness_days=21,
            rag=RAG.GREEN,
            description="GitHub Action composite action with Python packager and HMAC signing for DevSecOps evidence.",
        ),
        ProjectInfo(
            project_id="P5",
            name="Cloud Posture Snapshot",
            type=ProjectType.CLI,
            status=PS.COMPLETE,
            test_count=73,
            last_audit_date=_past(30),
            controls_covered=["Cloud Security", "Network Security", "Endpoint Security"],
            evidence_freshness_days=30,
            rag=RAG.AMBER,
            description="52 CIS checks across AWS, Azure, and GCP with PDF reporting.",
        ),
        ProjectInfo(
            project_id="P6",
            name="Policy-as-Code Starter Kit",
            type=ProjectType.CLI,
            status=PS.NEEDS_REVIEW,
            test_count=55,
            last_audit_date=_past(45),
            controls_covered=["IAM", "Network Security", "Cloud Security"],
            evidence_freshness_days=45,
            rag=RAG.AMBER,
            description="12 OPA Rego policies + Python evaluator for IAM least privilege, encryption, and logging.",
        ),
        ProjectInfo(
            project_id="P7",
            name="Security Metrics Pack",
            type=ProjectType.CLI,
            status=PS.COMPLETE,
            test_count=28,
            last_audit_date=_past(60),
            controls_covered=["SIEM & Monitoring"],
            evidence_freshness_days=60,
            rag=RAG.RED,
            description="MTTD/MTTR calculations, alert quality metrics, vuln SLA tracking with matplotlib charts.",
        ),
        ProjectInfo(
            project_id="P8",
            name="Data Classification Scanner",
            type=ProjectType.CLI,
            status=PS.COMPLETE,
            test_count=36,
            last_audit_date=_past(10),
            controls_covered=["Data Protection & DLP"],
            evidence_freshness_days=10,
            rag=RAG.GREEN,
            description="14 regex patterns for PII, PCI, PHI, and secrets detection with classification reports.",
        ),
        ProjectInfo(
            project_id="P9",
            name="Control Coverage Mapper",
            type=ProjectType.CLI,
            status=PS.COMPLETE,
            test_count=59,
            last_audit_date=_past(5),
            controls_covered=["Compliance", "IAM", "Data Protection & DLP"],
            evidence_freshness_days=5,
            rag=RAG.GREEN,
            description="Parses policy documents and maps controls across 4 frameworks with heatmap generation.",
        ),
        ProjectInfo(
            project_id="P10",
            name="Risk Register + Scoring Engine",
            type=ProjectType.CLI,
            status=PS.COMPLETE,
            test_count=63,
            last_audit_date=_past(12),
            controls_covered=["Risk Management", "Vulnerability Management"],
            evidence_freshness_days=12,
            rag=RAG.GREEN,
            description="CVSS v3.1 + SSVC v2 scoring engine with 5x5 risk matrix, CRUD, and acceptance workflows.",
        ),
        ProjectInfo(
            project_id="P11",
            name="Vendor Security Questionnaire",
            type=ProjectType.CLI,
            status=PS.NEEDS_REVIEW,
            test_count=31,
            last_audit_date=_past(50),
            controls_covered=["Supplier Security", "Data Protection & DLP"],
            evidence_freshness_days=50,
            rag=RAG.AMBER,
            description="Weighted scoring across 7 categories for third-party risk assessment questionnaires.",
        ),
        ProjectInfo(
            project_id="P12",
            name="Incident Response Runbook Gen",
            type=ProjectType.CLI,
            status=PS.COMPLETE,
            test_count=59,
            last_audit_date=_past(8),
            controls_covered=["Incident Response"],
            evidence_freshness_days=8,
            rag=RAG.GREEN,
            description="6 incident type templates with 230+ actions and AI-assisted customisation.",
        ),
    ]


def get_controls() -> list[ControlCoverage]:
    return [
        # IAM / Access Management
        ControlCoverage("C01", "User Registration & De-registration", "Access Control", ["P1", "P2", "P6"], CoverageStatus.COVERED, _past(14)),
        ControlCoverage("C02", "User Access Provisioning", "Access Control", ["P1", "P2"], CoverageStatus.COVERED, _past(14)),
        ControlCoverage("C03", "Privileged Access Management", "Access Control", ["P1", "P2", "P6"], CoverageStatus.COVERED, _past(7)),
        ControlCoverage("C04", "Access Rights Review", "Access Control", ["P2", "P9"], CoverageStatus.PARTIAL, _past(45)),
        ControlCoverage("C05", "Access Removal for Leavers", "Access Control", ["P2"], CoverageStatus.COVERED, _past(14)),
        ControlCoverage("C06", "Multi-Factor Authentication", "Access Control", ["P6"], CoverageStatus.PARTIAL, _past(45)),
        ControlCoverage("C07", "Secure Log-On Procedures", "Access Control", ["P1", "P6"], CoverageStatus.COVERED, _past(7)),
        # Endpoint Security
        ControlCoverage("C08", "Mobile Device Management", "Endpoint Security", ["P4", "P5"], CoverageStatus.COVERED, _past(21)),
        ControlCoverage("C09", "Anti-Malware Controls", "Endpoint Security", ["P4", "P5"], CoverageStatus.COVERED, _past(21)),
        ControlCoverage("C10", "Endpoint DLP", "Endpoint Security", ["P4"], CoverageStatus.PARTIAL, _past(30)),
        ControlCoverage("C11", "Endpoint Detection & Response (EDR)", "Endpoint Security", ["P4", "P5"], CoverageStatus.COVERED, _past(21)),
        # Network Security
        ControlCoverage("C12", "Remote Access", "Network Security", ["P5", "P6"], CoverageStatus.COVERED, _past(30)),
        ControlCoverage("C13", "Firewall Rule Management", "Network Security", ["P5", "P6"], CoverageStatus.COVERED, _past(30)),
        ControlCoverage("C14", "IDS/IPS", "Network Security", ["P5"], CoverageStatus.PARTIAL, _past(30)),
        ControlCoverage("C15", "Web Application Firewall (WAF)", "Network Security", ["P5", "P6"], CoverageStatus.COVERED, _past(30)),
        ControlCoverage("C16", "Network Segregation", "Network Security", ["P6"], CoverageStatus.PARTIAL, _past(45)),
        # Data Protection & DLP
        ControlCoverage("C17", "Email DLP", "Data Protection", ["P8", "P11"], CoverageStatus.COVERED, _past(10)),
        ControlCoverage("C18", "Information Classification", "Data Protection", ["P8", "P9"], CoverageStatus.COVERED, _past(5)),
        ControlCoverage("C19", "Removable Media Controls", "Data Protection", ["P8"], CoverageStatus.PARTIAL, _past(10)),
        ControlCoverage("C20", "Privacy & PII Protection", "Data Protection", ["P8", "P9", "P11"], CoverageStatus.COVERED, _past(5)),
        # Vulnerability Management
        ControlCoverage("C21", "Patch Management", "Vulnerability Management", ["P3", "P10"], CoverageStatus.COVERED, _past(3)),
        ControlCoverage("C22", "Technical Vulnerability Management", "Vulnerability Management", ["P3", "P10"], CoverageStatus.COVERED, _past(3)),
        ControlCoverage("C23", "Penetration Testing", "Vulnerability Management", ["P10"], CoverageStatus.PARTIAL, _past(12)),
        ControlCoverage("C24", "Hardening Standards Compliance", "Vulnerability Management", ["P5", "P6"], CoverageStatus.COVERED, _past(30)),
        # SIEM & Monitoring
        ControlCoverage("C25", "Security Event Logging", "SIEM & Monitoring", ["P2", "P3", "P7"], CoverageStatus.COVERED, _past(3)),
        ControlCoverage("C26", "Incident Event Management", "SIEM & Monitoring", ["P3", "P7"], CoverageStatus.PARTIAL, _past(60)),
        ControlCoverage("C27", "Alert Monitoring & Response", "SIEM & Monitoring", ["P7"], CoverageStatus.PARTIAL, _past(60)),
        # Incident Response
        ControlCoverage("C28", "Incident Response Plan", "Incident Response", ["P12"], CoverageStatus.COVERED, _past(8)),
        ControlCoverage("C29", "Incident Classification", "Incident Response", ["P12"], CoverageStatus.COVERED, _past(8)),
        # Supplier Security
        ControlCoverage("C30", "Supplier Security Agreements", "Supplier Security", ["P11"], CoverageStatus.PARTIAL, _past(50)),
        ControlCoverage("C31", "Supplier Service Monitoring", "Supplier Security", ["P11"], CoverageStatus.GAP, _past(0)),
        # Risk & Compliance
        ControlCoverage("C32", "Risk Assessment Framework", "Risk Management", ["P10"], CoverageStatus.COVERED, _past(12)),
        ControlCoverage("C33", "Policy-to-Control Mapping", "Compliance", ["P9"], CoverageStatus.COVERED, _past(5)),
        ControlCoverage("C34", "Audit Readiness Tracking", "Compliance", ["P13"], CoverageStatus.COVERED, TODAY.isoformat()),
    ]


def get_deadlines() -> list[Deadline]:
    return [
        Deadline(
            id="DL1",
            description="Annual IAM Control Review — Privileged Access Management (C03)",
            date=_d(14),
            days_remaining=14,
            related_control="C03",
            priority="HIGH",
        ),
        Deadline(
            id="DL2",
            description="Q2 Vulnerability Management Audit — Patch Compliance Reporting (C21/C22)",
            date=_d(21),
            days_remaining=21,
            related_control="C21",
            priority="HIGH",
        ),
        Deadline(
            id="DL3",
            description="Supplier Risk Re-assessment — Vendor Questionnaires due (C30/C31)",
            date=_d(35),
            days_remaining=35,
            related_control="C30",
            priority="MEDIUM",
        ),
        Deadline(
            id="DL4",
            description="Cloud Security Posture Review — CIS Benchmarks Refresh (C12/C13/C14)",
            date=_d(60),
            days_remaining=60,
            related_control="C12",
            priority="MEDIUM",
        ),
        Deadline(
            id="DL5",
            description="Data Privacy Compliance Check — PII Protection Review (C20)",
            date=_d(85),
            days_remaining=85,
            related_control="C20",
            priority="LOW",
        ),
    ]


def get_dashboard_data() -> DashboardData:
    projects = get_projects()
    controls = get_controls()
    deadlines = get_deadlines()

    green = sum(1 for p in projects if p.rag == RAG.GREEN)
    amber = sum(1 for p in projects if p.rag == RAG.AMBER)
    red = sum(1 for p in projects if p.rag == RAG.RED)

    covered = sum(1 for c in controls if c.status == CoverageStatus.COVERED)
    partial = sum(1 for c in controls if c.status == CoverageStatus.PARTIAL)
    gap = sum(1 for c in controls if c.status == CoverageStatus.GAP)

    # Overall RAG: worst of the project RAGs
    if red > 0:
        overall = RAG.RED
    elif amber > 0:
        overall = RAG.AMBER
    else:
        overall = RAG.GREEN

    summary = SummaryStats(
        total_projects=len(projects),
        total_tests=sum(p.test_count for p in projects),
        controls_covered=covered,
        controls_total=len(controls),
        controls_gap=gap,
        controls_partial=partial,
        upcoming_deadlines=len(deadlines),
        projects_green=green,
        projects_amber=amber,
        projects_red=red,
    )

    return DashboardData(
        projects=projects,
        controls=controls,
        deadlines=sorted(deadlines, key=lambda d: d.days_remaining),
        overall_rag=overall,
        summary=summary,
        generated_at=datetime.now().isoformat(),
    )
