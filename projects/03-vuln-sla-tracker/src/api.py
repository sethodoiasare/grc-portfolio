"""
FastAPI Application — Vuln SLA Tracker.

Endpoints for vulnerability management, scanner imports, SLA KPIs,
dashboard data, and breach reporting.
"""

from fastapi import FastAPI, HTTPException, Query, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from src.database import get_db, init_db, rows_to_list, row_to_dict
from src.auth import (
    LoginRequest, RegisterRequest, UserResponse,
    register_user, authenticate_user, create_access_token,
    get_current_user, require_admin,
)
from src.scanner_parser import parse_scanner_csv
from src.sla_engine import compute_vuln_sla, compute_kpis, get_top_overdue, get_breach_timeline
from src.models import severity_from_cvss, sla_deadline_days, Severity, VulnStatus

app = FastAPI(
    title="Vuln SLA Tracker API",
    description="Patch and vulnerability SLA breach tracking for Vodafone ITGC compliance",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


# ---------------------------------------------------------------------------
# Auth Routes
# ---------------------------------------------------------------------------


@app.post("/api/v1/auth/register", response_model=UserResponse)
def route_register(req: RegisterRequest):
    return register_user(req.email, req.password, "auditor")


@app.post("/api/v1/auth/register/admin", response_model=UserResponse)
def route_register_admin(req: RegisterRequest, admin: dict = Depends(require_admin)):
    return register_user(req.email, req.password, req.role)


@app.post("/api/v1/auth/login")
def route_login(req: LoginRequest):
    user = authenticate_user(req.email, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"], "role": user["role"]},
    }


@app.get("/api/v1/auth/me", response_model=UserResponse)
def route_me(user: dict = Depends(get_current_user)):
    return user


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/api/v1/health")
def route_health():
    conn = get_db()
    try:
        vuln_count = conn.execute("SELECT COUNT(*) FROM vulnerabilities").fetchone()[0]
        run_count = conn.execute("SELECT COUNT(*) FROM scanner_runs").fetchone()[0]
    finally:
        conn.close()
    return {"status": "ok", "version": "1.0.0", "vulnerabilities": vuln_count, "scanner_runs": run_count}


# ---------------------------------------------------------------------------
# Scanner Import
# ---------------------------------------------------------------------------


@app.post("/api/v1/scanner/import")
async def route_import_scanner(
    file: UploadFile = File(...),
    scanner_type: str = Query(..., description="nessus | openvas | qualys"),
    user: dict = Depends(get_current_user),
):
    if scanner_type not in ("nessus", "openvas", "qualys"):
        raise HTTPException(status_code=422, detail="scanner_type must be nessus, openvas, or qualys")

    try:
        content = (await file.read()).decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read file: {e}")

    try:
        vulns = parse_scanner_csv(scanner_type, file.filename or "upload.csv", content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Parse error: {e}")

    if not vulns:
        raise HTTPException(status_code=422, detail="No vulnerabilities found in file")

    now = datetime.utcnow().isoformat() + "Z"
    conn = get_db()
    try:
        run_cur = conn.execute(
            "INSERT INTO scanner_runs (scanner_type, filename) VALUES (?, ?)",
            (scanner_type, file.filename or "upload.csv"),
        )
        run_id = run_cur.lastrowid

        new_count = 0
        updated_count = 0
        for v in vulns:
            existing = conn.execute(
                """SELECT id FROM vulnerabilities
                   WHERE asset_hostname = ? AND title = ? AND port = ? AND status = 'open'""",
                (v.asset_hostname, v.title, v.port),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE vulnerabilities SET last_seen = ?, cvss_score = MAX(cvss_score, ?) WHERE id = ?",
                    (now, v.cvss_score, existing["id"]),
                )
                updated_count += 1
            else:
                conn.execute(
                    """INSERT INTO vulnerabilities
                       (scanner_run_id, scanner_type, asset_hostname, asset_ip, title,
                        description, severity, cvss_score, cve_id, port, protocol,
                        solution, first_seen, last_seen)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (run_id, scanner_type, v.asset_hostname, v.asset_ip, v.title,
                     v.description, v.severity, v.cvss_score, v.cve_id, v.port,
                     v.protocol, v.solution, now, now),
                )
                new_count += 1

        conn.execute(
            "UPDATE scanner_runs SET vulns_imported = ?, vulns_new = ?, vulns_updated = ? WHERE id = ?",
            (len(vulns), new_count, updated_count, run_id),
        )
        conn.commit()

        return {
            "run_id": run_id,
            "scanner_type": scanner_type,
            "filename": file.filename,
            "vulns_imported": len(vulns),
            "vulns_new": new_count,
            "vulns_updated": updated_count,
        }
    finally:
        conn.close()


@app.get("/api/v1/scanner/runs")
def route_scanner_runs():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM scanner_runs ORDER BY imported_at DESC LIMIT 50").fetchall()
        return rows_to_list(rows)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Vulnerabilities
# ---------------------------------------------------------------------------


@app.get("/api/v1/vulnerabilities")
def route_list_vulnerabilities(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    scanner_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sla_breach: Optional[str] = Query(None, description="breached | compliant"),
    sort_by: str = Query("first_seen_desc"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    conn = get_db()
    try:
        where = []
        params = []

        if status:
            where.append("status = ?")
            params.append(status)
        if severity:
            where.append("severity = ?")
            params.append(severity)
        if scanner_type:
            where.append("scanner_type = ?")
            params.append(scanner_type)
        if search:
            where.append("(asset_hostname LIKE ? OR title LIKE ? OR cve_id LIKE ?)")
            p = f"%{search}%"
            params.extend([p, p, p])

        if sla_breach:
            now = datetime.utcnow().isoformat()
            if sla_breach == "breached":
                where.append("""
                    status = 'open' AND first_seen IS NOT NULL
                    AND (
                        (severity = 'Critical' AND julianday(?) - julianday(first_seen) > 7)
                        OR (severity = 'High' AND julianday(?) - julianday(first_seen) > 30)
                        OR (severity = 'Medium' AND julianday(?) - julianday(first_seen) > 90)
                        OR (severity = 'Low' AND julianday(?) - julianday(first_seen) > 180)
                        OR (severity = 'Info' AND julianday(?) - julianday(first_seen) > 365)
                    )
                """)
                params.extend([now] * 5)
            elif sla_breach == "compliant":
                where.append("""
                    status != 'open' OR first_seen IS NULL
                    OR (
                        (severity = 'Critical' AND julianday(?) - julianday(first_seen) <= 7)
                        OR (severity = 'High' AND julianday(?) - julianday(first_seen) <= 30)
                        OR (severity = 'Medium' AND julianday(?) - julianday(first_seen) <= 90)
                        OR (severity = 'Low' AND julianday(?) - julianday(first_seen) <= 180)
                        OR (severity = 'Info' AND julianday(?) - julianday(first_seen) <= 365)
                    )
                """)
                params.extend([now] * 5)

        where_clause = ("WHERE " + " AND ".join(where)) if where else ""
        count_sql = f"SELECT COUNT(*) FROM vulnerabilities {where_clause}"
        count = conn.execute(count_sql, params).fetchone()[0]

        sort_map = {
            "first_seen_asc": "first_seen ASC",
            "first_seen_desc": "first_seen DESC",
            "cvss_desc": "cvss_score DESC",
            "cvss_asc": "cvss_score ASC",
            "hostname": "asset_hostname ASC",
        }
        order = sort_map.get(sort_by, "first_seen DESC")

        sql = f"SELECT * FROM vulnerabilities {where_clause} ORDER BY {order} LIMIT ? OFFSET ?"
        rows = conn.execute(sql, params + [limit, offset]).fetchall()

        results = []
        for r in rows_to_list(rows):
            results.append(compute_vuln_sla(r))

        return {"total": count, "limit": limit, "offset": offset, "items": results}
    finally:
        conn.close()


@app.get("/api/v1/vulnerabilities/{vuln_id}")
def route_get_vulnerability(vuln_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM vulnerabilities WHERE id = ?", (vuln_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Vulnerability not found")
        return compute_vuln_sla(dict(row))
    finally:
        conn.close()


class UpdateVulnRequest(BaseModel):
    status: Optional[str] = None


@app.patch("/api/v1/vulnerabilities/{vuln_id}")
def route_update_vulnerability(vuln_id: int, req: UpdateVulnRequest, user: dict = Depends(get_current_user)):
    if req.status and req.status not in ("open", "closed", "risk_accepted", "false_positive"):
        raise HTTPException(status_code=422, detail="Invalid status")

    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM vulnerabilities WHERE id = ?", (vuln_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Vulnerability not found")

        now = datetime.utcnow().isoformat() + "Z"
        if req.status == "closed":
            conn.execute(
                "UPDATE vulnerabilities SET status = ?, closed_at = ? WHERE id = ?",
                (req.status, now, vuln_id),
            )
        elif req.status == "risk_accepted":
            conn.execute(
                "UPDATE vulnerabilities SET status = ?, risk_accepted_at = ? WHERE id = ?",
                (req.status, now, vuln_id),
            )
        else:
            conn.execute("UPDATE vulnerabilities SET status = ? WHERE id = ?", (req.status, vuln_id))
        conn.commit()

        updated = conn.execute("SELECT * FROM vulnerabilities WHERE id = ?", (vuln_id,)).fetchone()
        return compute_vuln_sla(dict(updated))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Dashboard KPIs
# ---------------------------------------------------------------------------


@app.get("/api/v1/dashboard/kpis")
def route_dashboard_kpis():
    kpis = compute_kpis()
    return kpis.to_dict()


@app.get("/api/v1/dashboard/top-overdue")
def route_top_overdue(limit: int = Query(10)):
    return get_top_overdue(limit)


@app.get("/api/v1/dashboard/breach-timeline")
def route_breach_timeline(days: int = Query(90)):
    return get_breach_timeline(days)


@app.get("/api/v1/dashboard/severity-distribution")
def route_severity_distribution():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT severity, COUNT(*) as count FROM vulnerabilities WHERE status = 'open' GROUP BY severity ORDER BY count DESC"
        ).fetchall()
        return rows_to_list(rows)
    finally:
        conn.close()


@app.get("/api/v1/dashboard/scanner-summary")
def route_scanner_summary():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT scanner_type, COUNT(*) as total, SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) as open_count FROM vulnerabilities GROUP BY scanner_type"
        ).fetchall()
        return rows_to_list(rows)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


@app.get("/api/v1/export/vulnerabilities")
def route_export_csv(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
):
    import csv, io

    conn = get_db()
    try:
        where = []
        params = []
        if status:
            where.append("status = ?")
            params.append(status)
        if severity:
            where.append("severity = ?")
            params.append(severity)
        where_clause = ("WHERE " + " AND ".join(where)) if where else ""
        rows = conn.execute(f"SELECT * FROM vulnerabilities {where_clause} ORDER BY cvss_score DESC", params).fetchall()

        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows([dict(r) for r in rows])

        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vulnerabilities_export.csv"},
        )
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
