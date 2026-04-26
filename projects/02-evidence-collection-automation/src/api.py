"""
FastAPI Application — Evidence Collection Automator.

Exposes connectors, collections, evidence items, and bundle management
as REST endpoints. Reuses auth from Project 1.
"""

from fastapi import FastAPI, HTTPException, Query, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from src.database import get_db, init_db, ensure_evidence_store, rows_to_list
from src.auth import (
    LoginRequest, RegisterRequest, UserResponse,
    register_user, authenticate_user, create_access_token,
    get_current_user, require_admin,
)
from src.connectors import get_connector, CONNECTORS
from src.normalizer import (
    normalize_items, get_evidence_by_collection, get_all_evidence,
    get_evidence_stats, delete_evidence_item,
)
from src.bundler import (
    create_bundle, get_bundle, list_bundles,
    export_bundle_json, export_bundle_file, build_assessment_request,
)
from src.markets import list_markets, search_markets, create_market, delete_market, rename_market

app = FastAPI(
    title="Evidence Collection Automator API",
    description="Automated audit evidence collection for Vodafone ITGC assurance",
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
    ensure_evidence_store()
    init_db()


# ---------------------------------------------------------------------------
# Auth Routes
# ---------------------------------------------------------------------------


@app.post("/api/v1/auth/register", response_model=UserResponse)
def route_register(req: RegisterRequest):
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
def route_health():
    conn = get_db()
    try:
        connectors_count = conn.execute("SELECT COUNT(*) FROM connectors").fetchone()[0]
    finally:
        conn.close()
    return {
        "status": "ok",
        "version": "1.0.0",
        "connectors_loaded": connectors_count,
    }


# ---------------------------------------------------------------------------
# Markets (reused from P1)
# ---------------------------------------------------------------------------


@app.get("/api/v1/markets")
def route_list_markets():
    return list_markets()


@app.get("/api/v1/markets/search")
def route_search_markets(q: str = Query(..., description="Case-insensitive search")):
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


# ---------------------------------------------------------------------------
# Connectors
# ---------------------------------------------------------------------------


@app.get("/api/v1/connectors")
def route_list_connectors():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM connectors ORDER BY name").fetchall()
        return rows_to_list(rows)
    finally:
        conn.close()


class TriggerConnectorRequest(BaseModel):
    market_id: int | None = None
    config: dict = {}


@app.post("/api/v1/connectors/{connector_id}/run")
def route_trigger_connector(connector_id: int, req: TriggerConnectorRequest, user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        c = conn.execute("SELECT * FROM connectors WHERE id = ?", (connector_id,)).fetchone()
        if c is None:
            raise HTTPException(status_code=404, detail="Connector not found")

        connector = get_connector(c["connector_type"])
        if connector is None:
            raise HTTPException(status_code=500, detail=f"No implementation for connector type: {c['connector_type']}")

        # Mark as running
        conn.execute(
            "UPDATE connectors SET status = 'running' WHERE id = ?",
            (connector_id,),
        )
        conn.commit()

        # Get market name
        market_name = "Unknown"
        if req.market_id:
            market = conn.execute("SELECT name FROM markets WHERE id = ?", (req.market_id,)).fetchone()
            if market:
                market_name = market["name"]

        # Create collection record
        started_at = datetime.utcnow().isoformat() + "Z"
        cur = conn.execute(
            """INSERT INTO evidence_collections
               (connector_id, user_id, market_id, status, started_at)
               VALUES (?, ?, ?, 'running', ?)""",
            (connector_id, user["id"], req.market_id, started_at),
        )
        collection_id = cur.lastrowid
        conn.commit()

        # Run connector
        try:
            items = connector.run(req.config or {}, market_name)
        except Exception as e:
            conn.execute(
                "UPDATE connectors SET status = 'error' WHERE id = ?",
                (connector_id,),
            )
            conn.execute(
                "UPDATE evidence_collections SET status = 'error', completed_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat() + "Z", collection_id),
            )
            conn.commit()
            raise HTTPException(status_code=500, detail=f"Connector failed: {e}")

        # Normalize and save
        saved = normalize_items(items, collection_id)

        # Update records
        control_ids = list(set(cid for item in items for cid in item.control_mapping))
        conn.execute(
            """UPDATE connectors SET status = 'success', last_run = ? WHERE id = ?""",
            (datetime.utcnow().isoformat() + "Z", connector_id),
        )
        conn.execute(
            """UPDATE evidence_collections
               SET status = 'complete', completed_at = ?, evidence_count = ?,
                   control_ids = ?, summary_json = ?
               WHERE id = ?""",
            (
                datetime.utcnow().isoformat() + "Z",
                len(saved),
                json.dumps(control_ids),
                json.dumps({"connector": c["name"], "market": market_name, "items_collected": len(saved)}),
                collection_id,
            ),
        )
        conn.commit()

        return {
            "collection_id": collection_id,
            "connector": c["name"],
            "market": market_name,
            "items_collected": len(saved),
            "status": "complete",
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


@app.get("/api/v1/collections")
def route_list_collections(user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT ec.*, c.name as connector_name, m.name as market_name
               FROM evidence_collections ec
               JOIN connectors c ON ec.connector_id = c.id
               LEFT JOIN markets m ON ec.market_id = m.id
               WHERE ec.user_id = ?
               ORDER BY ec.started_at DESC LIMIT 50""",
            (user["id"],),
        ).fetchall()
        results = rows_to_list(rows)
        for r in results:
            r["control_ids"] = json.loads(r["control_ids"])
            r["summary"] = json.loads(r["summary_json"])
        return results
    finally:
        conn.close()


@app.get("/api/v1/collections/{collection_id}")
def route_get_collection(collection_id: int, user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT ec.*, c.name as connector_name, m.name as market_name
               FROM evidence_collections ec
               JOIN connectors c ON ec.connector_id = c.id
               LEFT JOIN markets m ON ec.market_id = m.id
               WHERE ec.id = ?""",
            (collection_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Collection not found")
        d = dict(row)
        d["control_ids"] = json.loads(d["control_ids"])
        d["summary"] = json.loads(d["summary_json"])
        d["evidence_items"] = get_evidence_by_collection(collection_id)
        return d
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Evidence Items
# ---------------------------------------------------------------------------


@app.get("/api/v1/evidence")
def route_list_evidence(
    connector_type: str | None = Query(None),
    market_id: int | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(100),
):
    return get_all_evidence(connector_type=connector_type, market_id=market_id, search=search, limit=limit)


@app.get("/api/v1/evidence/stats")
def route_evidence_stats():
    return get_evidence_stats()


@app.delete("/api/v1/evidence/{item_id}")
def route_delete_evidence(item_id: int, user: dict = Depends(get_current_user)):
    if not delete_evidence_item(item_id):
        raise HTTPException(status_code=404, detail="Evidence item not found")
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Bundles
# ---------------------------------------------------------------------------

class CreateBundleRequest(BaseModel):
    name: str
    item_ids: list[int]
    market_id: int | None = None
    control_ids: list[str] = []
    description: str = ""


@app.get("/api/v1/bundles")
def route_list_bundles(user: dict = Depends(get_current_user)):
    return list_bundles(user["id"])


@app.post("/api/v1/bundles")
def route_create_bundle(req: CreateBundleRequest, user: dict = Depends(get_current_user)):
    bundle = create_bundle(
        user_id=user["id"],
        name=req.name,
        item_ids=req.item_ids,
        market_id=req.market_id,
        control_ids=req.control_ids,
        description=req.description,
    )
    return bundle


@app.get("/api/v1/bundles/{bundle_id}")
def route_get_bundle(bundle_id: int):
    bundle = get_bundle(bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return bundle


@app.get("/api/v1/bundles/{bundle_id}/export")
def route_export_bundle(bundle_id: int):
    data = export_bundle_json(bundle_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@app.get("/api/v1/bundles/{bundle_id}/download")
def route_download_bundle(bundle_id: int):
    path = export_bundle_file(bundle_id)
    return FileResponse(path, media_type="application/json", filename=f"evidence_bundle_{bundle_id}.json")


@app.post("/api/v1/bundles/{bundle_id}/assess")
def route_assess_bundle(bundle_id: int, user: dict = Depends(get_current_user)):
    """Send a bundle to the ITGC Evidence Analyser (Project 1) for assessment."""
    payload = build_assessment_request(bundle_id)
    if "error" in payload:
        raise HTTPException(status_code=404, detail=payload["error"])
    return {
        "status": "ready_to_assess",
        "bundle_id": bundle_id,
        "assessment_count": len(payload.get("assessments", [])),
        "payload": payload,
        "note": "POST this payload to Project 1's /api/v1/assess/batch endpoint",
    }


# ---------------------------------------------------------------------------
# Manual File Upload (extracts text for evidence)
# ---------------------------------------------------------------------------


@app.post("/api/v1/evidence/upload")
async def route_upload_evidence(
    user: dict = Depends(get_current_user),
    market_id: int | None = Query(None),
    control_ids: str = Query(""),
    files: list[UploadFile] = File(...),
):
    from src.extractor import extract_file_text

    saved = []
    for f in files:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{f.filename or 'upload'}")
        try:
            tmp.write(await f.read())
            tmp.close()
            extracted_text = extract_file_text(tmp.name)

            conn = get_db()
            try:
                # Create a collection for this manual upload
                manual_conn = conn.execute(
                    "SELECT id FROM connectors WHERE connector_type = 'manual'"
                ).fetchone()
                if manual_conn:
                    cur = conn.execute(
                        """INSERT INTO evidence_collections
                           (connector_id, user_id, market_id, status, started_at, completed_at)
                           VALUES (?, ?, ?, 'complete', ?, ?)""",
                        (manual_conn["id"], user["id"], market_id,
                         datetime.utcnow().isoformat() + "Z",
                         datetime.utcnow().isoformat() + "Z"),
                    )
                    collection_id = cur.lastrowid

                    ctrl_list = [c.strip() for c in control_ids.split(",") if c.strip()]
                    conn.execute(
                        """INSERT INTO evidence_items
                           (collection_id, evidence_type, source_system, data_json,
                            normalized_at, freshness_date, control_mapping)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (collection_id, "manual_evidence", "Manual Upload",
                         json.dumps({"filename": f.filename, "text": extracted_text, "size": os.path.getsize(tmp.name)}),
                         datetime.utcnow().isoformat() + "Z",
                         (datetime.utcnow()).isoformat() + "Z",
                         json.dumps(ctrl_list)),
                    )
                    conn.execute(
                        "UPDATE evidence_collections SET evidence_count = 1 WHERE id = ?",
                        (collection_id,),
                    )
                    conn.commit()
                    saved.append({"filename": f.filename, "collection_id": collection_id})
            finally:
                conn.close()
        finally:
            os.unlink(tmp.name)

    return {"uploaded": len(saved), "files": saved}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
