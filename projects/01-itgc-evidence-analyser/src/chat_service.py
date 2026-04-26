"""
Chat Service for the ITGC Evidence Analyser.

Provides a conversational audit assistant backed by Claude with tool use.
The assistant can list assessments, inspect results, re-read evidence,
modify verdicts, and look up control definitions.
"""

import json
import os
from datetime import datetime

import anthropic

from src.database import get_db, rows_to_list, row_to_dict
from src.control_parser import ControlParser

SONNET = "claude-sonnet-4-6"

CHAT_SYSTEM_PROMPT = """You are the Vodafone ITGC Audit Assistant — an AI-powered audit quality reviewer embedded in the ITGC Evidence Analyser platform. You work alongside human auditors to double-check assessment outputs, re-examine evidence, and suggest amendments when the initial automated assessment may have missed something.

YOUR ROLE:
- Review completed assessments and their evidence
- Answer questions about control requirements and assessment findings
- Re-read evidence files when the auditor wants a second look
- Amend verdicts, confidence scores, and findings when the auditor identifies issues
- Maintain professional audit scepticism — never agree blindly

CAPABILITIES:
You have access to tools (function calling) that let you:
1. list_assessments — see all past assessments across all markets
2. get_assessment — get full detail for a specific assessment
3. reread_evidence — re-read the raw evidence text for any assessment
4. modify_verdict — update an assessment's verdict, confidence, gaps, and findings
5. get_control_detail — look up the actual D/E statement requirements for any control

WORKFLOW:
When an auditor asks about an assessment:
1. Use list_assessments or get_assessment to load the relevant assessment(s)
2. If they question the evidence assessment, use reread_evidence to check the raw text
3. If they identify a specific issue (e.g. "MFA was actually configured, see paragraph 3"), use modify_verdict to amend
4. Always explain what you found and what you changed, with specific references to the evidence

IMPORTANT RULES:
- Always verify by re-reading evidence before agreeing to change a verdict
- When modifying a verdict, provide a specific justification citing the evidence
- If the evidence genuinely supports the current verdict, say so professionally — do not change it just to agree
- Use precise audit terminology: observed, confirmed, absent, inconclusive, contradicted
- Be concise but thorough — the auditor is busy"""

TOOLS = [
    {
        "name": "list_assessments",
        "description": "List all past assessments. Use this to get an overview of what has been assessed, across all markets and controls.",
        "input_schema": {
            "type": "object",
            "properties": {
                "control_id": {
                    "type": "string",
                    "description": "Optional: filter by control ID (e.g. 'ENDPOINT_001'). Omit to list all.",
                },
                "market_id": {
                    "type": "integer",
                    "description": "Optional: filter by market ID. Omit to list all.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results. Default 20.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_assessment",
        "description": "Get the full detail of a specific assessment, including verdict, confidence, gaps, findings, and requirements assessment table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assessment_id": {
                    "type": "integer",
                    "description": "The ID of the assessment to retrieve.",
                },
            },
            "required": ["assessment_id"],
        },
    },
    {
        "name": "reread_evidence",
        "description": "Re-read the raw evidence text from all files that were uploaded for a specific assessment. Use this when the auditor questions whether the initial assessment correctly interpreted the evidence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assessment_id": {
                    "type": "integer",
                    "description": "The ID of the assessment whose evidence should be re-read.",
                },
            },
            "required": ["assessment_id"],
        },
    },
    {
        "name": "modify_verdict",
        "description": "Update an assessment's verdict, confidence, gaps, and findings. Use this when the auditor identifies an error in the initial automated assessment and the evidence supports a change. Only call this if you have reviewed the evidence and agree a change is warranted.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assessment_id": {
                    "type": "integer",
                    "description": "The ID of the assessment to modify.",
                },
                "new_verdict": {
                    "type": "string",
                    "enum": ["PASS", "PARTIAL", "FAIL", "INSUFFICIENT_EVIDENCE"],
                    "description": "The corrected verdict.",
                },
                "new_confidence": {
                    "type": "number",
                    "description": "Updated confidence score between 0.0 and 1.0.",
                },
                "justification": {
                    "type": "string",
                    "description": "Detailed justification for the change, citing specific evidence. This is an audit requirement — never skip this.",
                },
                "updated_gaps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Updated list of gaps. Replace the gaps list entirely — do not append.",
                },
                "updated_findings_summary": {
                    "type": "string",
                    "description": "Updated summary of findings reflecting the new verdict and evidence.",
                },
            },
            "required": ["assessment_id", "new_verdict", "new_confidence", "justification"],
        },
    },
    {
        "name": "get_control_detail",
        "description": "Look up the full D (design) and E (evidence) statement requirements for a specific Vodafone ITGC control.",
        "input_schema": {
            "type": "object",
            "properties": {
                "control_id": {
                    "type": "string",
                    "description": "The control ID to look up, e.g. 'ENDPOINT_001' or 'IAM_001'.",
                },
            },
            "required": ["control_id"],
        },
    },
]


class ChatService:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.parser = ControlParser()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_message(self, user_id: int, session_id: int | None, message: str) -> dict:
        """Send a message and get the assistant response. Creates a new session if needed."""
        conn = get_db()
        try:
            if session_id is None:
                cur = conn.execute(
                    "INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)",
                    (user_id, message[:80] if len(message) > 80 else message),
                )
                conn.commit()
                session_id = cur.lastrowid

            conn.execute(
                "INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, "user", message),
            )
            conn.commit()

            history = self._load_history(conn, session_id)

            response_content, tool_results = self._call_claude(conn, user_id, history)

            tool_json = json.dumps(tool_results) if tool_results else None
            conn.execute(
                "INSERT INTO chat_messages (session_id, role, content, tool_calls_json) VALUES (?, ?, ?, ?)",
                (session_id, "assistant", response_content, tool_json),
            )
            conn.commit()

            return {
                "session_id": session_id,
                "message": {
                    "role": "assistant",
                    "content": response_content,
                    "tool_calls": tool_results,
                },
            }
        finally:
            conn.close()

    def list_sessions(self, user_id: int) -> list[dict]:
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
            return rows_to_list(rows)
        finally:
            conn.close()

    def get_messages(self, user_id: int, session_id: int) -> list[dict]:
        conn = get_db()
        try:
            session = conn.execute(
                "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id),
            ).fetchone()
            if session is None:
                return []
            rows = conn.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
            msgs = rows_to_list(rows)
            for m in msgs:
                if m.get("tool_calls_json"):
                    try:
                        m["tool_calls"] = json.loads(m["tool_calls_json"])
                    except json.JSONDecodeError:
                        m["tool_calls"] = None
                    del m["tool_calls_json"]
            return msgs
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Claude interaction
    # ------------------------------------------------------------------

    def _load_history(self, conn, session_id: int) -> list[dict]:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
        messages = []
        for r in rows:
            messages.append({"role": r["role"], "content": r["content"]})
        return messages

    def _call_claude(self, conn, user_id: int, history: list[dict]) -> tuple[str, list[dict] | None]:
        tool_results: list[dict] = []

        messages = [{"role": m["role"], "content": m["content"]} for m in history]

        for _ in range(6):
            response = self.client.messages.create(
                model=SONNET,
                max_tokens=4096,
                system=CHAT_SYSTEM_PROMPT,
                messages=messages,
                tools=TOOLS,
            )

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b for b in response.content if b.type == "text"]

            if not tool_uses:
                return "\n".join(t.text for t in text_blocks), (tool_results or None)

            messages.append({"role": "assistant", "content": response.content})
            tool_result_blocks = []

            for tool in tool_uses:
                result = self._execute_tool(conn, user_id, tool.name, tool.input)
                tool_results.append({"tool": tool.name, "input": tool.input, "result": result})
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tool.id,
                    "content": json.dumps(result, default=str),
                })

            messages.append({"role": "user", "content": tool_result_blocks})

        text = "\n".join(t.text for t in text_blocks) if text_blocks else "I've completed the review."
        return text, tool_results

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def _execute_tool(self, conn, user_id: int, tool_name: str, args: dict) -> dict:
        if tool_name == "list_assessments":
            return self._tool_list_assessments(conn, user_id, args)
        elif tool_name == "get_assessment":
            return self._tool_get_assessment(conn, user_id, args)
        elif tool_name == "reread_evidence":
            return self._tool_reread_evidence(conn, args)
        elif tool_name == "modify_verdict":
            return self._tool_modify_verdict(conn, user_id, args)
        elif tool_name == "get_control_detail":
            return self._tool_get_control_detail(args)
        return {"error": f"Unknown tool: {tool_name}"}

    def _tool_list_assessments(self, conn, user_id: int, args: dict) -> dict:
        query = """SELECT a.id, a.control_id, a.statement_type, a.verdict,
                          a.created_at, a.market_id, m.name as market_name
                   FROM assessments a
                   LEFT JOIN markets m ON a.market_id = m.id
                   WHERE a.user_id = ?"""
        params: list = [user_id]
        if args.get("control_id"):
            query += " AND a.control_id = ?"
            params.append(args["control_id"])
        if args.get("market_id"):
            query += " AND a.market_id = ?"
            params.append(args["market_id"])
        query += " ORDER BY a.created_at DESC LIMIT ?"
        params.append(args.get("limit", 20))

        rows = conn.execute(query, params).fetchall()
        return {"assessments": rows_to_list(rows), "count": len(rows)}

    def _tool_get_assessment(self, conn, user_id: int, args: dict) -> dict:
        row = conn.execute(
            """SELECT a.*, m.name as market_name
               FROM assessments a LEFT JOIN markets m ON a.market_id = m.id
               WHERE a.id = ? AND a.user_id = ?""",
            (args["assessment_id"], user_id),
        ).fetchone()
        if row is None:
            return {"error": f"Assessment {args['assessment_id']} not found or not yours"}
        d = dict(row)
        if d.get("result_json"):
            try:
                d["result"] = json.loads(d["result_json"])
            except json.JSONDecodeError:
                pass
        return d

    def _tool_reread_evidence(self, conn, args: dict) -> dict:
        rows = conn.execute(
            """SELECT filename, content_type, extracted_text, created_at
               FROM evidence_files WHERE assessment_id = ?
               ORDER BY created_at""",
            (args["assessment_id"],),
        ).fetchall()
        if not rows:
            assess = conn.execute(
                "SELECT evidence_text FROM assessments WHERE id = ?",
                (args["assessment_id"],),
            ).fetchone()
            return {"files": [], "note": "No separate evidence files found for this assessment."}

        files = []
        all_text = []
        for r in rows:
            files.append({"filename": r["filename"], "content_type": r["content_type"]})
            if r["extracted_text"]:
                all_text.append(f"=== {r['filename']} ===\n{r['extracted_text']}")

        return {"files": files, "extracted_text": "\n\n".join(all_text)}

    def _tool_modify_verdict(self, conn, user_id: int, args: dict) -> dict:
        assessment_id = args["assessment_id"]
        existing = conn.execute(
            "SELECT * FROM assessments WHERE id = ?", (assessment_id,)
        ).fetchone()
        if existing is None:
            return {"error": f"Assessment {assessment_id} not found"}

        result_json = existing["result_json"]
        try:
            result = json.loads(result_json)
        except json.JSONDecodeError:
            result = {}

        result["verdict"] = args["new_verdict"]
        result["confidence"] = args["new_confidence"]
        if "updated_gaps" in args:
            result["gaps"] = args["updated_gaps"]
        if "updated_findings_summary" in args and result.get("draft_finding"):
            result["draft_finding"]["observation"] = args["updated_findings_summary"]

        result["_amended_by"] = user_id
        result["_amended_at"] = datetime.utcnow().isoformat()
        result["_amendment_justification"] = args.get("justification", "")

        conn.execute(
            """UPDATE assessments SET verdict = ?, result_json = ?
               WHERE id = ?""",
            (args["new_verdict"], json.dumps(result), assessment_id),
        )
        conn.commit()

        return {"status": "updated", "assessment_id": assessment_id, "new_verdict": args["new_verdict"]}

    def _tool_get_control_detail(self, args: dict) -> dict:
        control = self.parser.get_control(args["control_id"])
        if not control:
            return {"error": f"Control '{args['control_id']}' not found"}
        return {
            "control_id": control["control_id"],
            "control_name": control["control_name"],
            "domain": control.get("domain", ""),
            "vodafone_standard": control.get("vodafone_standard", ""),
            "d_statements": control.get("d_statements", []),
            "e_statements": control.get("e_statements", []),
        }
