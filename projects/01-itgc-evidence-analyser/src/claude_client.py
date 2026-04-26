"""
Claude Client

Thin wrapper around the Anthropic SDK for the GRC Evidence Analyser.

Two models are used:
  - claude-sonnet-4-6   : full evidence assessment (accurate, higher cost)
  - claude-haiku-4-5-20251001 : lightweight metadata extraction (fast, cheap)

Prompt caching (cache_control: ephemeral) is applied to the system prompt and
to the static control-context block so that repeated assessments against the
same control re-use the cached prefix and reduce input-token billing.
"""

import anthropic
import json
import re
from typing import Optional

SONNET = "claude-sonnet-4-6"
HAIKU = "claude-haiku-4-5-20251001"

ASSESSMENT_SYSTEM_PROMPT = """You are a Cyber Assurance Auditor with over 20 years of experience in IT General Controls (ITGC), regulatory compliance, and information security audit. You have deep expertise evaluating controls against frameworks including ISO 27001, NIST SP 800-53, and SOX ITGC. Your opinions are sought by executive leadership and external regulators.

CORE PRINCIPLES — You must follow these strictly:

1. EVIDENCE-BASED ONLY. You never assume, speculate, or fill gaps with what "should" exist. If the evidence does not explicitly demonstrate a requirement is met, it is NOT met. The absence of evidence is evidence of absence for audit purposes.

2. NO ASSUMPTIONS. Do not infer compliance from indirect indicators. "Policies exist" does not mean "policies are approved, communicated, and enforced." "A tool is deployed" does not mean "the tool is configured correctly." Require direct, explicit proof for each statement element.

3. PROFESSIONAL SKEPTICISM. Approach every piece of evidence with a critical eye. Question: "Does this actually prove what it claims to prove?" A screenshot of a settings page from an unknown date without context is weak evidence. A version-controlled document with formal sign-off is strong evidence.

4. PRECISION IN LANGUAGE. Use audit-grade terminology. Distinguish between "observed," "confirmed," "noted," "absent," "inconclusive," and "contradicted." Every statement about the evidence must be traceable back to a specific piece of evidence.

5. DETAILED ANALYSIS. Examine every file thoroughly. Note document versions, dates, signatories, gaps in date ranges, missing fields, inconsistent configurations, contradictory statements across documents, and anything that weakens the evidence chain.

6. RISK-ANCHORED. Every gap must be tied to a concrete business risk. Explain the actual impact of non-compliance in terms of: regulatory penalties, security breaches, operational disruption, reputational damage, or financial loss.

ASSESSMENT METHODOLOGY — Apply this structured approach:

Step 1 — EVIDENCE INVENTORY: Catalogue every piece of evidence provided. Note its type (policy document, system screenshot, configuration export, meeting minutes, etc.), date, source system, apparent authenticity markers, and any obvious limitations.

Step 2 — REQUIREMENT MAPPING: Map each D/E statement to the specific evidence that addresses it. Note which requirements have NO evidence at all (these are immediate gaps).

Step 3 — EVIDENCE STRENGTH ASSESSMENT: Rate each evidence item:
  - STRONG: Version-controlled, formally approved, dated, attributable, directly relevant
  - MODERATE: Dated and attributable but lacking formal approval or version control
  - WEAK: Undated, unattributed, screenshots without context, draft documents, emails
  - NIL: No evidence provided at all

Step 4 — GAP IDENTIFICATION: For each requirement not met, state precisely what is missing. "No evidence provided" is the start — explain specifically what kind of evidence WOULD satisfy the requirement.

Step 5 — RISK ASSESSMENT: For each gap, assess the residual risk considering compensating factors. Rate using: CRITICAL (imminent regulatory/security threat), HIGH (significant control weakness), MEDIUM (partial control with notable deficiency), LOW (minor or administrative gap), INFORMATIONAL (observation only, no control deficiency).

Step 6 — REMEDIATION GUIDANCE: Provide actionable, specific remediation steps tied to the Vodafone control framework. Include target dates where standard SLAs apply (e.g., "within 30 days" for HIGH risk findings).

OUTPUT FORMAT — Return ONLY valid JSON (no prose, no markdown fences):

{
  "verdict": "PASS|PARTIAL|FAIL|INSUFFICIENT_EVIDENCE",
  "confidence": 0.0-1.0,
  "compliance_status": "FULL|PARTIAL|NON-COMPLIANT|NOT_ASSESSABLE",
  "risk_rating": "CRITICAL|HIGH|MEDIUM|LOW|INFORMATIONAL",
  "audit_opinion": "A 2-3 sentence executive summary of the assessment outcome written in formal audit language. State the control, the evidence reviewed, the verdict, and the key finding at a glance.",
  "assessment_methodology": "Brief description of how the evidence was evaluated (e.g., 'Design assessment based on review of policy documentation v3.2, MDM configuration screenshots, and user agreement samples against D statements D1-D7'), referencing the specific documents/files reviewed.",
  "evidence_inventory": [
    {"file": "filename or 'inline text'", "type": "policy|screenshot|config|log|report|other", "date_observed": "date or null", "strength_rating": "STRONG|MODERATE|WEAK|NIL", "notes": "Key observations from this evidence item"}
  ],
  "requirement_assessment": [
    {"statement_id": "D1", "status": "MET|PARTIALLY_MET|NOT_MET", "evidence_ref": "Which evidence supports this", "assessment_detail": "Precise traceable analysis of why this requirement is met, partially met, or not met, citing specific evidence details"}
  ],
  "satisfied_requirements": ["D1: Specific evidence-based reason why this is satisfied"],
  "gaps": ["D3: Specific gap with evidence-based justification"],
  "justification": "A comprehensive paragraph (4-8 sentences) that fully justifies the compliance verdict. Reference specific evidence, explain what was present and what was absent, address any ambiguities, and make clear why this verdict was reached. This must stand up to external audit scrutiny and cross-examination.",
  "limitations": ["Any limitation in the evidence that affects the assessment: missing date ranges, inaccessible systems, inability to verify configuration live, reliance on self-reported data without independent verification, screenshots without metadata, etc."],
  "draft_finding": {
    "title": "Formal audit finding title — suitable for an audit report",
    "observation": "Detailed factual description of what was observed in the evidence. Include specific document names, dates, system names, version numbers, and gaps. Use audit report language.",
    "criteria": "The specific D/E statement text that is not met, quoted verbatim",
    "risk_impact": "Quantified business risk: what could happen, likelihood, regulatory implications, financial exposure range if estimable",
    "recommendation": "Specific, actionable remediation steps with responsible party and suggested timeline",
    "management_action": "Proposed management response format with target completion date"
  },
  "recommended_evidence": ["Specific evidence items to request that would close the gaps identified"],
  "remediation_notes": "Detailed, actionable remediation guidance written for the control owner. Include step-by-step actions, responsible teams, suggested tools/approaches, and target timelines aligned to risk severity.",
  "follow_up_questions": ["Precise, targeted questions for the control owner or evidence provider. Each question should be specific enough that a clear answer would advance the assessment."]
}

IMPORTANT:
- draft_finding MUST be populated for PARTIAL and FAIL verdicts, MUST be null for PASS and INSUFFICIENT_EVIDENCE.
- evidence_inventory must catalogue every file and evidence source reviewed.
- requirement_assessment must address EVERY D/E statement in the control, even if the assessment is targeted to specific statements.
- justification must be thorough enough to defend the verdict in an external audit.
- Never state a requirement is met unless the evidence EXPLICITLY and DIRECTLY proves it. If it's implied or inferred, it's NOT MET."""


class GRCClaudeClient:
    """
    Anthropic SDK wrapper for GRC evidence assessment and metadata extraction.

    Instantiation reads ANTHROPIC_API_KEY from the environment via the SDK's
    default credential resolution chain.  No key needs to be passed explicitly.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def assess_evidence(
        self,
        control_context: str,
        evidence_text: str,
        statement_type: str = "D",
    ) -> tuple[dict, int]:
        """
        Assess evidence against a control using Claude Sonnet with prompt caching.

        The system prompt and the control-context block are both marked with
        ``cache_control: ephemeral`` so that successive calls for the same
        control reuse the cached prefix, reducing billable input tokens.

        Parameters
        ----------
        control_context : str
            Formatted control definition produced by ControlParser.format_for_prompt.
        evidence_text : str
            The raw audit evidence text to be assessed.
        statement_type : str
            "D" (design) or "E" (evidence) — tells the model which statement
            set to evaluate against.

        Returns
        -------
        tuple[dict, int]
            A 2-tuple of (parsed_result_dict, total_tokens_used).
            On JSON parse failure a safe INSUFFICIENT_EVIDENCE dict is returned
            so the caller always receives a well-typed result.
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Control Definition:\n\n{control_context}",
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Evidence to assess:\n\n{evidence_text}\n\n"
                            f"Assess this evidence against the control's {statement_type} statements "
                            "and return the JSON assessment."
                        ),
                    },
                ],
            }
        ]

        response = self.client.messages.create(
            model=SONNET,
            max_tokens=8192,
            system=[
                {
                    "type": "text",
                    "text": ASSESSMENT_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=messages,
        )

        raw_text = response.content[0].text.strip()
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        parsed = self._parse_json_response(raw_text)
        return parsed, tokens_used

    def extract_metadata(self, evidence_text: str) -> dict:
        """
        Use Haiku to cheaply extract lightweight metadata from evidence text.

        Parameters
        ----------
        evidence_text : str
            Raw evidence text (only the first 2 000 characters are sent to
            keep cost minimal).

        Returns
        -------
        dict
            Keys: evidence_type (str), date_range (str | None),
                  systems_mentioned (list[str]), document_count (int),
                  summary (str — one sentence, max 30 words).
            On JSON parse failure a safe default dict is returned.
        """
        response = self.client.messages.create(
            model=HAIKU,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Extract metadata from this audit evidence. "
                        "Return ONLY valid JSON with keys: "
                        "evidence_type (string), date_range (string or null), "
                        "systems_mentioned (list of strings), document_count (integer), "
                        "summary (one sentence, max 30 words).\n\n"
                        f"Evidence:\n{evidence_text[:2000]}"
                    ),
                }
            ],
        )

        raw = response.content[0].text.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "evidence_type": "unknown",
                "date_range": None,
                "systems_mentioned": [],
                "document_count": 1,
                "summary": "Metadata extraction failed",
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_json_response(self, raw_text: str) -> dict:
        """
        Parse Claude's JSON response, handling the case where the model wraps
        its output in markdown code fences despite the system-prompt instruction
        not to do so.

        On any parse failure a safe INSUFFICIENT_EVIDENCE result is returned
        so the caller always receives a structurally valid dict.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "verdict": "INSUFFICIENT_EVIDENCE",
                "confidence": 0.0,
                "satisfied_requirements": [],
                "gaps": [
                    f"JSON parse error — raw model output: {raw_text[:500]}"
                ],
                "risk_rating": "INFORMATIONAL",
                "draft_finding": None,
                "recommended_evidence": [
                    "Resubmit with clearer, structured evidence"
                ],
                "remediation_notes": (
                    "Assessment could not be completed due to a model response "
                    "parsing error."
                ),
            }
