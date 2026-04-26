"""
Control Parser

Provides lookup, filtering, and prompt-formatting utilities over the CONTROLS
dataset. The ControlParser is the primary interface for all other modules that
need to query or render control definitions.
"""

from src.controls_data import CONTROLS
from typing import Optional


class ControlParser:
    def __init__(self):
        self._controls: dict[str, dict] = {c["control_id"]: c for c in CONTROLS}

    def get_control(self, control_id: str) -> Optional[dict]:
        """Return the control dict for the given control_id, or None if not found."""
        return self._controls.get(control_id)

    def list_controls(self) -> list[dict]:
        """Return all controls as a list of dicts."""
        return list(self._controls.values())

    def get_by_domain(self, domain: str) -> list[dict]:
        """Return all controls belonging to the given domain (case-sensitive)."""
        return [c for c in self._controls.values() if c["domain"] == domain]

    def search(self, query: str) -> list[dict]:
        """
        Case-insensitive full-text search across control name, D statements,
        and E statements. Returns all controls where the query substring is found.
        """
        q = query.lower()
        results = []
        for c in self._controls.values():
            searchable = (
                c["control_name"].lower()
                + " "
                + " ".join(s["text"] for s in c["d_statements"] + c["e_statements"])
            )
            if q in searchable:
                results.append(c)
        return results

    def format_for_prompt(
        self, control_id: str, statement_type: str = "D",
        target_statements: list[str] | None = None,
    ) -> str:
        """
        Returns the control as clean, structured text suitable for injection
        into a Claude prompt.

        Parameters
        ----------
        control_id : str
            The control identifier, e.g. "IAM_001".
        statement_type : str
            "D"    — design statements only
            "E"    — evidence statements only
            "both" — both design and evidence statements
        target_statements : list[str] | None
            Optional list of specific D/E statement IDs to include
            (e.g., ["D1", "E1"]). When None or empty, all statements are included.

        Raises
        ------
        ValueError
            If the control_id is not found in the controls dataset.
        """
        c = self.get_control(control_id)
        if not c:
            raise ValueError(f"Control {control_id} not found")

        target_set = set(target_statements) if target_statements else set()
        use_targeted = bool(target_set)

        lines = [
            f"Control: {c['control_id']} — {c['control_name']}",
            f"Standard: {c['vodafone_standard']}",
            f"Domain: {c['domain']}",
        ]
        if use_targeted:
            lines.append(f"Targeted Statements: {', '.join(sorted(target_set))}")
        lines.append("")

        if statement_type in ("D", "both"):
            d_list = [s for s in c["d_statements"]
                      if not use_targeted or s["id"] in target_set]
            if d_list:
                scope = f"(targeted {len(d_list)} of {len(c['d_statements'])})" if use_targeted else ""
                lines.append(f"Design Requirements (D Statements) {scope}:")
                for s in d_list:
                    lines.append(f"  {s['id']}: {s['text']}")
                lines.append("")

        if statement_type in ("E", "both"):
            e_list = [s for s in c["e_statements"]
                      if not use_targeted or s["id"] in target_set]
            if e_list:
                scope = f"(targeted {len(e_list)} of {len(c['e_statements'])})" if use_targeted else ""
                lines.append(f"Evidence Requirements (E Statements) {scope}:")
                for s in e_list:
                    lines.append(f"  {s['id']}: {s['text']}")

        return "\n".join(lines)
