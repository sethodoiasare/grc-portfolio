"""
FastAPI Application

Exposes the ITGC Evidence Analyser as an HTTP API. All assessment logic is
delegated to the existing EvidenceAssessor, ControlParser, and ReportGenerator
components -- this module is purely a transport/routing layer.

Routes
------
GET  /api/v1/health                  -- liveness check
POST /api/v1/auth/register           -- register a new user
POST /api/v1/auth/login              -- login, receive JWT
GET  /api/v1/auth/me                 -- current user info
GET  /api/v1/controls                -- list all controls (optional ?domain= filter)
GET  /api/v1/controls/search         -- full-text search across controls (?q=)
GET  /api/v1/controls/{control_id}   -- fetch a single control definition
POST /api/v1/assess                  -- assess evidence text against a control
POST /api/v1/assess/upload           -- assess an uploaded evidence file
POST /api/v1/assess/upload/multi     -- assess text + multiple evidence files together
POST /api/v1/assess/upload/xlsx      -- upload an XLSX with controls+evidence for batch assessment
POST /api/v1/assess/batch            -- batch assessment returning JSON report
POST /api/v1/assess/batch/pdf        -- batch assessment returning PDF file
POST /api/v1/assess/pdf              -- assess evidence text and return PDF report
POST /api/v1/reports/pdf             -- generate PDF from an existing assessment result

Run locally:
    uvicorn src.api:app --reload --port 8001
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime

from src.assessor import EvidenceAssessor
from src.control_parser import ControlParser
from src.report_generator import ReportGenerator
from src.models import StatementType
from src.database import get_db, init_db, ensure_evidence_store
from src.markets import list_markets, search_markets, create_market, delete_market, rename_market
from src.samples import get_samples, save_samples, get_all_for_market
from src.chat_service import ChatService
from src.auth import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
    register_user,
    authenticate_user,
    create_access_token,
    get_current_user,
    require_admin,
)

app = FastAPI(
    title="ITGC Evidence Analyser API",
    description="AI-powered audit evidence assessment against Vodafone ITGC controls",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_assessor = EvidenceAssessor()
_parser = ControlParser()
_generator = ReportGenerator()
_chat = ChatService()


@app.on_event("startup")
def _startup():
    ensure_evidence_store()
    init_db()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class AssessRequest(BaseModel):
    control_id: str
    evidence_text: str
    statement_type: str = "D"
    target_statements: list[str] = []
    market_id: int | None = None
    samples: list[str] = []


class BatchAssessItem(BaseModel):
    control_id: str
    evidence_text: str
    statement_type: str = "D"
    target_statements: list[str] = []


class BatchAssessRequest(BaseModel):
    audit_scope: str
    assessments: list[BatchAssessItem]


class ReportRequest(BaseModel):
    result: dict


# ---------------------------------------------------------------------------
# Auth Routes
# ---------------------------------------------------------------------------


@app.post("/api/v1/auth/register", response_model=UserResponse)
def route_register(req: RegisterRequest):
    # Public registration — anyone can create an auditor account.
    # Admin account creation requires an existing admin's token.
    user = register_user(req.email, req.password, "auditor")
    return user


@app.post("/api/v1/auth/register/admin", response_model=UserResponse)
def route_register_admin(req: RegisterRequest, admin: dict = Depends(require_admin)):
    user = register_user(req.email, req.password, req.role)
    return user


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
async def health():
    return {
        "status": "ok",
        "version": "1.1.0",
        "controls_loaded": len(_parser.list_controls()),
    }


# ---------------------------------------------------------------------------
# Markets
# ---------------------------------------------------------------------------


@app.get("/api/v1/markets")
def route_list_markets():
    return list_markets()


@app.get("/api/v1/markets/search")
def route_search_markets(q: str = Query(..., description="Case-insensitive search query")):
    return search_markets(q)


@app.post("/api/v1/markets")
def route_create_market(req: dict, admin: dict = Depends(require_admin)):
    name = req.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="name is required")
    market = create_market(name, admin["id"])
    if market is None:
        raise HTTPException(status_code=409, detail="Market already exists")
    return market


@app.delete("/api/v1/markets/{market_id}")
def route_delete_market(market_id: int, admin: dict = Depends(require_admin)):
    if not delete_market(market_id):
        raise HTTPException(status_code=404, detail="Market not found")
    return {"status": "deleted"}


@app.patch("/api/v1/markets/{market_id}")
def route_rename_market(market_id: int, req: dict, admin: dict = Depends(require_admin)):
    name = req.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="name is required")
    market = rename_market(market_id, name)
    if market is None:
        raise HTTPException(status_code=404, detail="Market not found")
    return market


# ---------------------------------------------------------------------------
# Samples
# ---------------------------------------------------------------------------

class SaveSamplesRequest(BaseModel):
    market_id: int
    control_id: str
    tags: list[str] = []


@app.get("/api/v1/samples")
def route_get_samples(market_id: int = Query(...), control_id: str = Query(...)):
    result = get_samples(market_id, control_id)
    if result is None:
        return {"market_id": market_id, "control_id": control_id, "tags": []}
    return result


@app.put("/api/v1/samples")
def route_save_samples(req: SaveSamplesRequest, user: dict = Depends(get_current_user)):
    return save_samples(req.market_id, req.control_id, req.tags, user["id"])


@app.get("/api/v1/samples/all")
def route_get_all_samples(market_id: int = Query(...)):
    return get_all_for_market(market_id)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@app.get("/api/v1/search")
def route_unified_search(q: str = Query(...), type: str = Query("all")):
    results: dict[str, list] = {}
    if type in ("all", "controls"):
        results["controls"] = _parser.search(q)
    if type in ("all", "markets"):
        results["markets"] = search_markets(q)
    return results


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------


@app.get("/api/v1/controls")
async def list_controls(domain: str | None = Query(None)):
    if domain:
        return _parser.get_by_domain(domain)
    return _parser.list_controls()


@app.get("/api/v1/controls/search")
async def search_controls(q: str = Query(..., description="Case-insensitive search query")):
    return _parser.search(q)


@app.get("/api/v1/controls/{control_id}")
async def get_control(control_id: str):
    ctrl = _parser.get_control(control_id)
    if not ctrl:
        raise HTTPException(status_code=404, detail=f"Control '{control_id}' not found")
    return ctrl


# ---------------------------------------------------------------------------
# Assessment
# ---------------------------------------------------------------------------


@app.post("/api/v1/assess")
async def assess_evidence(req: AssessRequest, user: dict = Depends(get_current_user)):
    if req.statement_type not in ("D", "E"):
        raise HTTPException(status_code=422, detail="statement_type must be 'D' or 'E'")

    try:
        result = _assessor.assess(
            control_id=req.control_id,
            evidence_text=req.evidence_text,
            statement_type=req.statement_type,
            target_statements=req.target_statements or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Persist assessment (non-fatal if DB write fails)
    try:
        _save_assessment(user["id"], req, result)
    except Exception as e:
        import traceback
        traceback.print_exc()

    return result.to_dict()


@app.post("/api/v1/assess/upload/multi")
async def assess_multi_upload(
    user: dict = Depends(get_current_user),
    control_id: str = Query(...),
    statement_type: str = Query("D"),
    target_statements: str = Query(""),
    evidence_text: str = Query(""),
    market_id: int | None = Query(None),
    samples: str = Query(""),
    files: list[UploadFile] = File(...),
):
    if statement_type not in ("D", "E"):
        raise HTTPException(status_code=422, detail="statement_type must be 'D' or 'E'")

    combined = evidence_text
    saved_files = []
    tmp_paths: list[str] = []
    for f in files:
        try:
            safe_suffix = "".join(c for c in (f.filename or "evidence") if c.isalnum() or c in "._-")[:40]
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{safe_suffix}")
            tmp_paths.append(tmp.name)
            tmp.write(await f.read())
            tmp.close()
            extracted = _assessor.extract_file_text(tmp.name)
            combined += f"\n\n--- File: {f.filename} ---\n{extracted}"
            saved_files.append((f.filename, f.content_type, tmp.name, extracted))
        except Exception as e:
            # Clean up temp files on failure
            for p in tmp_paths:
                try:
                    os.unlink(p)
                except Exception:
                    pass
            raise HTTPException(status_code=400, detail=f"Failed to process file '{f.filename}': {e}")

    # Truncate combined evidence if it exceeds ~150K chars (roughly 50K tokens)
    MAX_EVIDENCE_CHARS = 150_000
    if len(combined) > MAX_EVIDENCE_CHARS:
        combined = combined[:MAX_EVIDENCE_CHARS] + f"\n\n[... truncated {len(combined) - MAX_EVIDENCE_CHARS} characters to stay within model limits]"

    targets = [t.strip() for t in target_statements.split(",") if t.strip()] if target_statements else None
    sample_list = [s.strip() for s in samples.split(",") if s.strip()] if samples else []

    try:
        result = _assessor.assess(control_id, combined, statement_type, targets)
    except ValueError as e:
        for p in tmp_paths:
            try:
                os.unlink(p)
            except Exception:
                pass
        raise HTTPException(status_code=404, detail=str(e))

    result_dict = result.to_dict()
    try:
        _save_assessment_with_files(user["id"], control_id, statement_type, market_id, sample_list, result_dict, saved_files)
    except Exception as e:
        import traceback
        traceback.print_exc()
        for p in tmp_paths:
            try:
                os.unlink(p)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to save assessment: {e}")

    return result_dict


@app.post("/api/v1/assess/upload")
async def assess_with_file(
    user: dict = Depends(get_current_user),
    control_id: str = Query(...),
    statement_type: str = Query("D"),
    target_statements: str = Query(""),
    market_id: int | None = Query(None),
    samples: str = Query(""),
    file: UploadFile = File(...),
):
    if statement_type not in ("D", "E"):
        raise HTTPException(status_code=422, detail="statement_type must be 'D' or 'E'")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename or 'evidence'}")
    try:
        tmp.write(await file.read())
        tmp.close()
        targets = [t.strip() for t in target_statements.split(",") if t.strip()] if target_statements else None
        result = _assessor.assess_from_file(control_id, tmp.name, statement_type, targets)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        os.unlink(tmp.name)

    sample_list = [s.strip() for s in samples.split(",") if s.strip()] if samples else []
    result_dict = result.to_dict()
    _save_assessment(user["id"], AssessRequest(
        control_id=control_id, evidence_text="", statement_type=statement_type,
        target_statements=targets or [], market_id=market_id, samples=sample_list,
    ), result)

    return result_dict


@app.post("/api/v1/assess/upload/xlsx")
async def assess_xlsx_upload(
    user: dict = Depends(get_current_user),
    file: UploadFile = File(...),
):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    try:
        tmp.write(await file.read())
        tmp.close()
        import pandas as pd
        df = pd.read_excel(tmp.name)
        items = []
        for _, row in df.iterrows():
            items.append({
                "control_id": str(row.get("control_id", "")),
                "evidence_text": str(row.get("evidence_text", "")),
                "statement_type": str(row.get("statement_type", "D")),
            })
        results = _assessor.assess_batch(items)
    finally:
        os.unlink(tmp.name)

    for r in results:
        _save_assessment(user["id"], AssessRequest(
            control_id=r.control_id, evidence_text="",
            statement_type=r.statement_type.value,
        ), r)

    return _generator.generate_json_report(results, "XLSX Batch", f"batch_{datetime.utcnow().isoformat()}")


@app.post("/api/v1/assess/batch")
async def assess_batch(req: BatchAssessRequest, user: dict = Depends(get_current_user)):
    results = _assessor.assess_batch([a.model_dump() for a in req.assessments])
    for r in results:
        _save_assessment(user["id"], AssessRequest(
            control_id=r.control_id, evidence_text="",
            statement_type=r.statement_type.value,
        ), r)
    return _generator.generate_json_report(
        results, req.audit_scope, f"batch_{datetime.utcnow().isoformat()}"
    )


@app.post("/api/v1/assess/batch/pdf")
async def assess_batch_pdf(req: BatchAssessRequest):
    results = _assessor.assess_batch([a.model_dump() for a in req.assessments])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        tmp.close()
        _generator.generate_pdf_report([r.to_dict() for r in results], req.audit_scope, tmp.name)
        return FileResponse(tmp.name, media_type="application/pdf", filename="itgc_batch_report.pdf")
    finally:
        pass


@app.post("/api/v1/assess/pdf")
async def assess_pdf(req: AssessRequest, user: dict = Depends(get_current_user)):
    if req.statement_type not in ("D", "E"):
        raise HTTPException(status_code=422, detail="statement_type must be 'D' or 'E'")

    try:
        result = _assessor.assess(
            control_id=req.control_id,
            evidence_text=req.evidence_text,
            statement_type=req.statement_type,
            target_statements=req.target_statements or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    _save_assessment(user["id"], req, result)

    # Inject market + samples for PDF display
    result_dict = result.to_dict()
    if req.market_id:
        conn = get_db()
        try:
            market = conn.execute("SELECT name FROM markets WHERE id = ?", (req.market_id,)).fetchone()
            if market:
                result_dict["market_name"] = market["name"]
        finally:
            conn.close()
    result_dict["samples"] = req.samples or []

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        tmp.close()
        _generator.generate_single_pdf(result_dict, tmp.name)
        safe_id = req.control_id.replace("/", "_").replace("\\", "_")
        return FileResponse(tmp.name, media_type="application/pdf", filename=f"itgc_{safe_id}_{result.verdict.value}.pdf")
    finally:
        pass


@app.post("/api/v1/reports/pdf")
async def generate_report_pdf(req: ReportRequest):
    result = req.result
    if isinstance(result, dict) and "control_id" in result:
        pass
    else:
        raise HTTPException(status_code=422, detail="result must contain at least control_id")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        tmp.close()
        _generator.generate_single_pdf(result, tmp.name)
        safe_id = result["control_id"].replace("/", "_").replace("\\", "_")
        verdict = result.get("verdict", "RESULT")
        return FileResponse(tmp.name, media_type="application/pdf", filename=f"itgc_{safe_id}_{verdict}.pdf")
    finally:
        pass


# ---------------------------------------------------------------------------
# Assessments (persisted)
# ---------------------------------------------------------------------------


@app.get("/api/v1/assessments")
def route_list_assessments(
    user: dict = Depends(get_current_user),
    market_id: int | None = Query(None),
    control_id: str | None = Query(None),
    search: str | None = Query(None),
):
    conn = get_db()
    try:
        query = """
            SELECT a.*, m.name as market_name
            FROM assessments a
            LEFT JOIN markets m ON a.market_id = m.id
            WHERE a.user_id = ?
        """
        params: list = [user["id"]]

        if market_id:
            query += " AND a.market_id = ?"
            params.append(market_id)
        if control_id:
            query += " AND a.control_id = ?"
            params.append(control_id)
        if search:
            query += """ AND (
                a.control_id LIKE ? OR
                m.name LIKE ? OR
                a.verdict LIKE ?
            )"""
            like = f"%{search}%"
            params.extend([like, like, like])

        query += " ORDER BY a.created_at DESC LIMIT 200"

        rows = conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if d.get("result_json"):
                try:
                    result = json.loads(d["result_json"])
                    result["id"] = d["id"]
                    result["market_id"] = d.get("market_id")
                    result["market_name"] = d.get("market_name")
                    result["samples"] = json.loads(d.get("samples_json", "[]"))
                    result["user_id"] = d["user_id"]
                    result["created_at"] = d["created_at"]
                    results.append(result)
                except json.JSONDecodeError:
                    pass
        return results
    finally:
        conn.close()


@app.delete("/api/v1/assessments/{assessment_id}")
def route_delete_assessment(assessment_id: int, user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, user_id FROM assessments WHERE id = ?", (assessment_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Assessment not found")
        if row["user_id"] != user["id"] and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not your assessment")

        conn.execute("DELETE FROM evidence_files WHERE assessment_id = ?", (assessment_id,))
        conn.execute("DELETE FROM assessments WHERE id = ?", (assessment_id,))
        conn.commit()
        return {"status": "deleted"}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatSendRequest(BaseModel):
    session_id: int | None = None
    message: str


@app.post("/api/v1/chat/send")
def route_chat_send(req: ChatSendRequest, user: dict = Depends(get_current_user)):
    if not req.message.strip():
        raise HTTPException(status_code=422, detail="message is required")
    return _chat.send_message(user["id"], req.session_id, req.message)


@app.get("/api/v1/chat/sessions")
def route_chat_sessions(user: dict = Depends(get_current_user)):
    return _chat.list_sessions(user["id"])


@app.get("/api/v1/chat/sessions/{session_id}/messages")
def route_chat_messages(session_id: int, user: dict = Depends(get_current_user)):
    return _chat.get_messages(user["id"], session_id)


# ---------------------------------------------------------------------------
# Assessment Persistence Helpers
# ---------------------------------------------------------------------------

def _save_assessment(user_id: int, req: AssessRequest, result) -> int:
    result_dict = result.to_dict()
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO assessments (user_id, market_id, control_id, statement_type,
               samples_json, verdict, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, req.market_id, req.control_id, req.statement_type,
                json.dumps(req.samples or []), result_dict.get("verdict", "UNKNOWN"),
                json.dumps(result_dict),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _save_assessment_with_files(user_id: int, control_id: str, statement_type: str,
                                 market_id: int | None, samples: list[str],
                                 result_dict: dict, files: list[tuple]) -> int:
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO assessments (user_id, market_id, control_id, statement_type,
               samples_json, verdict, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, market_id, control_id, statement_type,
                json.dumps(samples), result_dict.get("verdict", "UNKNOWN"),
                json.dumps(result_dict),
            ),
        )
        assessment_id = cur.lastrowid

        assess_dir = Path(os.environ.get("EVIDENCE_STORE", "data/evidence")) / str(assessment_id)
        assess_dir.mkdir(parents=True, exist_ok=True)

        for filename, content_type, src_path, extracted in files:
            dest_path = assess_dir / (filename or "evidence")
            os.rename(src_path, str(dest_path))
            conn.execute(
                """INSERT INTO evidence_files (assessment_id, filename, content_type, file_path, extracted_text)
                   VALUES (?, ?, ?, ?, ?)""",
                (assessment_id, filename, content_type, str(dest_path), extracted),
            )

        conn.commit()
        return assessment_id
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
