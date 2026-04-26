"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  ChevronDown,
  ChevronRight,
  ArrowRight,
  Shield,
  Calendar,
  Target,
  AlertTriangle,
  CheckCircle,
  Search,
  ClipboardCheck,
  Download,
  Loader2,
  Trash2,
  X,
  Globe,
  MapPin,
  Filter,
} from "lucide-react";
import { VerdictBadge } from "../_components/VerdictBadge";
import { RiskBadge } from "../_components/RiskBadge";
import { useAuth } from "../_hooks/useAuth";

interface EvidenceItem {
  file: string;
  type: string;
  date_observed: string | null;
  strength_rating: string;
  notes: string;
}

interface RequirementAssessment {
  statement_id: string;
  status: string;
  evidence_ref: string;
  assessment_detail: string;
}

interface AssessmentResult {
  id: number;
  control_id: string;
  control_name: string;
  statement_type: string;
  verdict: string;
  confidence: number;
  satisfied_requirements: string[];
  gaps: string[];
  risk_rating: string;
  draft_finding: {
    title: string;
    observation: string;
    criteria: string;
    risk_impact: string;
    recommendation: string;
    management_action: string;
  } | null;
  recommended_evidence: string[];
  remediation_notes: string;
  follow_up_questions: string[];
  compliance_status: string;
  audit_opinion: string;
  assessment_methodology: string;
  evidence_inventory: EvidenceItem[];
  requirement_assessment: RequirementAssessment[];
  justification: string;
  limitations: string[];
  assessed_at: string;
  tokens_used: number;
  model_used: string;
  market_id?: number;
  market_name?: string;
  samples?: string[];
  created_at?: string;
}

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.04 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 400, damping: 30 } },
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-GB", {
      day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function AssessmentCard({
  result,
  onDelete,
}: {
  result: AssessmentResult;
  onDelete: (id: number) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const { token } = useAuth();

  const handleDownloadPdf = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setPdfLoading(true);
    try {
      const res = await fetch("/api/v1/reports/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ result }),
      });
      if (!res.ok) throw new Error("PDF generation failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `itgc_${result.control_id}_${result.verdict}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silent
    } finally {
      setPdfLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    try {
      await fetch(`/api/v1/assessments/${result.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      onDelete(result.id);
    } catch {
      // silent
    }
  };

  return (
    <motion.div variants={item} className="glass overflow-hidden">
      {/* Header */}
      <button
        onClick={() => {
          setExpanded(!expanded);
          setConfirmDelete(false);
        }}
        className="w-full p-5 flex items-center gap-4 text-left hover:bg-[var(--surface-hover)]/50 transition-colors duration-200"
      >
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{
            backgroundColor:
              result.verdict === "PASS"
                ? "rgba(38, 201, 99, 0.1)"
                : result.verdict === "PARTIAL"
                ? "rgba(245, 166, 35, 0.1)"
                : result.verdict === "FAIL"
                ? "rgba(240, 68, 68, 0.1)"
                : "rgba(107, 114, 128, 0.1)",
          }}
        >
          {result.verdict === "PASS" ? (
            <CheckCircle className="w-5 h-5 text-[var(--pass)]" />
          ) : result.verdict === "FAIL" ? (
            <AlertTriangle className="w-5 h-5 text-[var(--fail)]" />
          ) : (
            <Shield className="w-5 h-5 text-[var(--partial)]" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-[var(--fg)] truncate">
              {result.control_name}
            </span>
            <VerdictBadge verdict={result.verdict} />
            <RiskBadge rating={result.risk_rating} />
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs text-[var(--muted)]">
            <span className="font-mono">{result.control_id}</span>
            {result.market_name && (
              <>
                <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {result.market_name}
                </span>
              </>
            )}
            <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {formatDate(result.created_at || result.assessed_at)}
            </span>
            <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
            <span>{(result.confidence * 100).toFixed(0)}% confidence</span>
          </div>
          {result.samples && result.samples.length > 0 && (
            <div className="flex items-center gap-1.5 mt-1.5">
              {result.samples.map((s, i) => (
                <span
                  key={i}
                  className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--accent)]/10 text-[var(--accent)]"
                >
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
          <span
            onClick={handleDownloadPdf}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === "Enter") handleDownloadPdf(e as unknown as React.MouseEvent); }}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-[var(--accent)]/10 hover:bg-[var(--accent)]/20 text-[var(--accent)] ring-1 ring-[var(--accent)]/15 transition-all ${pdfLoading ? "opacity-50 pointer-events-none" : "cursor-pointer"}`}
          >
            {pdfLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
            PDF
          </span>

          <button
            onClick={handleDelete}
            className={`inline-flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs font-medium transition-all ${
              confirmDelete
                ? "bg-[var(--fail)]/15 text-[var(--fail)] ring-1 ring-[var(--fail)]/25"
                : "text-[var(--muted)] hover:text-[var(--fail)] hover:bg-[var(--fail)]/5"
            }`}
            title={confirmDelete ? "Click again to confirm" : "Delete assessment"}
          >
            {confirmDelete ? <AlertTriangle className="w-3 h-3" /> : <Trash2 className="w-3 h-3" />}
          </button>
        </div>

        <motion.div animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }} className="shrink-0">
          <ChevronDown className="w-5 h-5 text-[var(--muted)]" />
        </motion.div>
      </button>

      {/* Expanded detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-4 border-t border-[var(--border)] pt-4">
              {/* Finding */}
              {result.draft_finding && (
                <div className="p-4 rounded-lg bg-[var(--surface-hover)]/50 ring-1 ring-[var(--border)]">
                  <p className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wide mb-2">Audit Finding</p>
                  <div className="space-y-2">
                    {result.draft_finding.title && (
                      <p className="text-sm font-bold text-[var(--fg)]">{result.draft_finding.title}</p>
                    )}
                    {result.draft_finding.observation && (
                      <p className="text-xs text-[var(--fg)]"><span className="font-medium text-[var(--muted)]">Observation: </span>{result.draft_finding.observation}</p>
                    )}
                    {result.draft_finding.criteria && (
                      <p className="text-xs text-[var(--fg)]"><span className="font-medium text-[var(--muted)]">Criteria: </span>{result.draft_finding.criteria}</p>
                    )}
                    {result.draft_finding.recommendation && (
                      <p className="text-xs text-[var(--fg)]"><span className="font-medium text-[var(--muted)]">Recommendation: </span>{result.draft_finding.recommendation}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Gaps */}
              {(result.gaps?.length ?? 0) > 0 && (
                <div>
                  <p className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wide mb-1.5">Compliance Gaps</p>
                  <ul className="list-disc list-inside space-y-0.5">
                    {(result.gaps ?? []).map((g, i) => <li key={i} className="text-xs text-[var(--fg)]">{g}</li>)}
                  </ul>
                </div>
              )}

              {/* Requirements Assessment */}
              {(result.requirement_assessment?.length ?? 0) > 0 && (
                <div>
                  <p className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wide mb-2">Requirements Assessment</p>
                  <div className="rounded-lg border border-[var(--border)] overflow-hidden">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-[var(--surface-hover)]">
                          <th className="text-left p-3 font-medium text-[var(--muted)]">ID</th>
                          <th className="text-left p-3 font-medium text-[var(--muted)]">Status</th>
                          <th className="text-left p-3 font-medium text-[var(--muted)]">Evidence Ref</th>
                          <th className="text-left p-3 font-medium text-[var(--muted)]">Detail</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(result.requirement_assessment ?? []).map((ra, i) => (
                          <tr key={i} className="border-t border-[var(--border)]">
                            <td className="p-3 font-mono text-[var(--accent)]">{ra.statement_id}</td>
                            <td className="p-3">{ra.status}</td>
                            <td className="p-3 text-[var(--muted)]">{ra.evidence_ref || "—"}</td>
                            <td className="p-3 text-[var(--muted)]">{ra.assessment_detail}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Meta */}
              <div className="flex items-center gap-3 text-xs text-[var(--muted)]/60 pt-2 border-t border-[var(--border)]">
                <span>Type: {result.statement_type === "D" ? "Design" : "Evidence"}</span>
                <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
                <span>Model: {result.model_used || "—"}</span>
                <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
                <span>Tokens: {result.tokens_used?.toLocaleString() || "—"}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function AssessmentsPage() {
  const [results, setResults] = useState<AssessmentResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const { token } = useAuth();

  useEffect(() => {
    fetch("/api/v1/assessments", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => setResults(Array.isArray(data) ? data : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token]);

  const filtered = useMemo(() => {
    if (!search.trim()) return results;
    const q = search.toLowerCase();
    return results.filter(
      (r) =>
        r.control_id?.toLowerCase().includes(q) ||
        r.control_name?.toLowerCase().includes(q) ||
        r.market_name?.toLowerCase().includes(q) ||
        r.verdict?.toLowerCase().includes(q) ||
        r.samples?.some((s) => s.toLowerCase().includes(q))
    );
  }, [results, search]);

  function removeResult(id: number) {
    setResults((prev) => prev.filter((r) => r.id !== id));
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass p-5">
              <div className="flex items-center gap-4">
                <div className="skeleton w-10 h-10 rounded-xl" />
                <div className="flex-1 space-y-2">
                  <div className="skeleton w-48 h-4 rounded" />
                  <div className="skeleton w-32 h-3 rounded" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <motion.div
      className="max-w-5xl mx-auto px-6 py-10"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Header */}
      <motion.div variants={item} className="mb-8">
        <motion.div
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-4"
          style={{ background: "rgba(91, 141, 239, 0.08)", color: "var(--accent)", border: "1px solid rgba(91, 141, 239, 0.15)" }}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, type: "spring", stiffness: 500 }}
        >
          <ClipboardCheck className="w-3 h-3" />
          Audit Trail
        </motion.div>
        <h1 className="text-4xl font-bold tracking-[-0.03em] text-[var(--fg)] leading-tight">
          Assessment
          <br />
          <span className="text-[var(--muted)]">History</span>
        </h1>
        <p className="text-sm text-[var(--muted)] mt-3">
          {results.length} assessment{results.length !== 1 ? "s" : ""} in your workspace
        </p>
      </motion.div>

      {/* Search */}
      <motion.div variants={item} className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)] w-4 h-4" />
          <input
            type="text"
            placeholder="Search by control, market, verdict..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] placeholder:text-[var(--muted)]/50 outline-none focus:border-[var(--accent)] transition-colors"
          />
          {search && (
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)] hover:text-[var(--fg)]"
              onClick={() => setSearch("")}
            >
              <X size={14} />
            </button>
          )}
        </div>
        {search && (
          <p className="text-xs text-[var(--muted)] mt-2">
            {filtered.length} of {results.length} assessment{filtered.length !== 1 ? "s" : ""} matching &quot;{search}&quot;
          </p>
        )}
      </motion.div>

      {/* List */}
      {results.length === 0 ? (
        <motion.div variants={item} className="text-center py-20">
          <FileText size={40} className="mx-auto mb-4 text-[var(--muted)]/30" />
          <p className="text-sm text-[var(--muted)] mb-3">No assessments yet.</p>
          <Link
            href="/assess"
            className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-semibold hover:bg-[var(--accent-soft)] transition-colors"
          >
            <ClipboardCheck size={16} />
            Run your first assessment
          </Link>
        </motion.div>
      ) : filtered.length === 0 ? (
        <motion.div variants={item} className="text-center py-20">
          <Search size={40} className="mx-auto mb-4 text-[var(--muted)]/30" />
          <p className="text-sm text-[var(--muted)]">No assessments match your search.</p>
          <button onClick={() => setSearch("")} className="mt-2 text-xs text-[var(--accent)] hover:underline">
            Clear search
          </button>
        </motion.div>
      ) : (
        <motion.div className="space-y-3">
          {filtered.map((r, i) => (
            <AssessmentCard key={r.id || i} result={r} onDelete={removeResult} />
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}
