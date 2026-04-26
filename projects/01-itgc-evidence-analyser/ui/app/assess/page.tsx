"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import {
  Shield,
  ClipboardCheck,
  Upload,
  X,
  Loader2,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ShieldAlert,
  FileUp,
  Trash,
  Sparkles,
  Download,
} from "lucide-react";
import { VerdictBadge } from "../_components/VerdictBadge";
import { RiskBadge } from "../_components/RiskBadge";
import { MarketSelector } from "../_components/MarketSelector";
import { SampleEditor } from "../_components/SampleEditor";
import { useAuth } from "../_hooks/useAuth";

const API = "/api/v1";

interface Statement {
  id: string;
  text: string;
}

interface Control {
  control_id: string;
  control_name: string;
  domain: string;
  d_statements: Statement[];
  e_statements: Statement[];
}

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
}

function AssessContent() {
  const searchParams = useSearchParams();
  const preselectedControl = searchParams.get("control") || "";

  const [controls, setControls] = useState<Control[]>([]);
  const [activeTab, setActiveTab] = useState<"single" | "batch" | "xlsx">("single");

  // Single assessment state
  const [controlId, setControlId] = useState(preselectedControl);
  const [evidenceText, setEvidenceText] = useState("");
  const [statementType, setStatementType] = useState("D");
  const [targetStatements, setTargetStatements] = useState<Set<string>>(new Set());

  // Batch state
  const [batchItems, setBatchItems] = useState<{ control_id: string; evidence_text: string; statement_type: string }[]>([]);
  const [batchControlId, setBatchControlId] = useState("");
  const [batchEvidence, setBatchEvidence] = useState("");

  // Shared state
  const [loading, setLoading] = useState(false);
  const [evidenceFiles, setEvidenceFiles] = useState<File[]>([]);
  const [dragOver, setDragOver] = useState(false);

  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [batchResults, setBatchResults] = useState<AssessmentResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Market + Samples
  const [selectedMarket, setSelectedMarket] = useState<{ id: number; name: string } | null>(null);
  const [samples, setSamples] = useState<string[]>([]);
  const { token } = useAuth();

  useEffect(() => {
    fetch(`${API}/controls`)
      .then((r) => r.json())
      .then(setControls)
      .catch(() => {});
  }, []);

  // Persist results to local storage
  useEffect(() => {
    if (result) {
      const stored = JSON.parse(localStorage.getItem("assessment_results") || "[]");
      const updated = [result, ...stored].slice(0, 50);
      localStorage.setItem("assessment_results", JSON.stringify(updated));
    }
  }, [result]);

  useEffect(() => {
    if (batchResults.length > 0) {
      const stored = JSON.parse(localStorage.getItem("assessment_results") || "[]");
      const updated = [...batchResults, ...stored].slice(0, 50);
      localStorage.setItem("assessment_results", JSON.stringify(updated));
    }
  }, [batchResults]);

  const runSingleAssess = async () => {
    if (!controlId) return;
    if (!evidenceText.trim() && evidenceFiles.length === 0) return;
    if (!token) {
      setError("Not authenticated. Please log in again.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const ts = [...targetStatements].join(",");
      const marketId = selectedMarket?.id ?? null;
      const samplesStr = samples.join(",");
      let res: Response;

      if (evidenceFiles.length > 0) {
        const formData = new FormData();
        evidenceFiles.forEach((f) => formData.append("files", f));
        const params = new URLSearchParams({
          control_id: controlId,
          statement_type: statementType,
          target_statements: ts,
          evidence_text: evidenceText,
          ...(marketId ? { market_id: String(marketId) } : {}),
          ...(samplesStr ? { samples: samplesStr } : {}),
        });
        // Call backend directly for multipart uploads — Next.js proxy breaks them
        const baseUrl = typeof window !== "undefined" ? "http://localhost:8001" : "";
        res = await fetch(`${baseUrl}/api/v1/assess/upload/multi?${params}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
      } else {
        res = await fetch(`${API}/assess`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            control_id: controlId,
            evidence_text: evidenceText,
            statement_type: statementType,
            target_statements: [...targetStatements],
            market_id: marketId,
            samples,
          }),
        });
      }

      if (!res.ok) {
        const text = await res.text();
        try {
          const err = JSON.parse(text);
          throw new Error(err.detail || `Server error (${res.status})`);
        } catch {
          throw new Error(`Server error (${res.status}): ${text.slice(0, 200)}`);
        }
      }
      const data: AssessmentResult = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const runBatchAssess = async () => {
    if (batchItems.length === 0) return;
    setLoading(true);
    setError(null);
    setBatchResults([]);
    try {
      const res = await fetch(`${API}/assess/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          audit_scope: "ITGC Evidence Assessment",
          assessments: batchItems,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Batch assessment failed");
      }
      const data = await res.json();
      setBatchResults(data.all_results || data.results || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const addBatchItem = () => {
    if (!batchControlId || !batchEvidence.trim()) return;
    setBatchItems((prev) => [
      ...prev,
      { control_id: batchControlId, evidence_text: batchEvidence, statement_type: "D" },
    ]);
    setBatchControlId("");
    setBatchEvidence("");
  };

  const removeBatchItem = (index: number) => {
    setBatchItems((prev) => prev.filter((_, i) => i !== index));
  };

  // XLSX state
  const [xlsxFile, setXlsxFile] = useState<File | null>(null);
  const [xlsxDrag, setXlsxDrag] = useState(false);

  const runXlsxAssess = async () => {
    if (!xlsxFile) return;
    setLoading(true);
    setError(null);
    setBatchResults([]);
    try {
      const formData = new FormData();
      formData.append("file", xlsxFile);
      const res = await fetch(`${API}/assess/upload/xlsx`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "XLSX upload failed");
      }
      const data = await res.json();
      setBatchResults(data.all_results || data.results || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const selectedControl = useMemo(
    () => controls.find((c) => c.control_id === controlId),
    [controls, controlId]
  );

  const verdictSummary = useMemo(() => {
    const counts = { PASS: 0, PARTIAL: 0, FAIL: 0, INSUFFICIENT_EVIDENCE: 0 };
    batchResults.forEach((r) => counts[r.verdict as keyof typeof counts]++);
    return counts;
  }, [batchResults]);

  const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.05, delayChildren: 0.05 } },
  };
  const fadeItem = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 400, damping: 30 } },
  };

  return (
    <motion.div
      className="max-w-6xl mx-auto px-6 py-10"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Header */}
      <motion.div variants={fadeItem} className="mb-8">
        <motion.div
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-4"
          style={{ background: "rgba(91, 141, 239, 0.08)", color: "var(--accent)", border: "1px solid rgba(91, 141, 239, 0.15)" }}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, type: "spring", stiffness: 500 }}
        >
          <Sparkles className="w-3 h-3" />
          Evidence Assessment
        </motion.div>
        <h1 className="text-4xl font-bold tracking-[-0.03em] text-[var(--fg)] leading-tight">
          Run
          <br />
          <span className="text-[var(--muted)]">Assessment</span>
        </h1>
        <p className="text-sm text-[var(--muted)] mt-3 max-w-md leading-relaxed">
          AI-powered evidence evaluation against Vodafone ITGC controls with detailed audit opinions.
        </p>
      </motion.div>

      {/* Tabs — matching TopNav pill design */}
      <motion.div variants={fadeItem} className="flex gap-1 mb-8 bg-[var(--surface)] p-1 rounded-lg w-fit">
        <LayoutGroup>
          {(["single", "batch", "xlsx"] as const).map((tab) => (
            <motion.button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`relative px-4 py-2 text-sm rounded-md transition-colors duration-200 capitalize ${
                activeTab === tab
                  ? "text-[var(--fg)] font-medium"
                  : "text-[var(--muted)] hover:text-[var(--fg)]"
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
            >
              {tab === "single" ? <ClipboardCheck className="w-3.5 h-3.5 inline mr-1.5" /> : null}
              {tab === "batch" ? <Upload className="w-3.5 h-3.5 inline mr-1.5" /> : null}
              {tab === "xlsx" ? <FileUp className="w-3.5 h-3.5 inline mr-1.5" /> : null}
              {tab === "xlsx" ? "XLSX" : tab}
              {activeTab === tab && (
                <motion.div
                  layoutId="assess-tab-pill"
                  className="absolute inset-0 rounded-md bg-[var(--accent)]/10 ring-1 ring-[var(--accent)]/15"
                  transition={{ type: "spring", stiffness: 500, damping: 35 }}
                />
              )}
            </motion.button>
          ))}
        </LayoutGroup>
      </motion.div>

      {/* Single Assessment */}
      {activeTab === "single" && (
        <div className="space-y-6">
          <div className="glass p-6">
            {/* Market selector */}
            <div className="mb-4">
              <label className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider block mb-2">
                Market
              </label>
              <MarketSelector value={selectedMarket} onChange={setSelectedMarket} />
            </div>

            {/* Control selector */}
            <div className="mb-4">
              <label className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider block mb-2">
                Target Control
              </label>
              <select
                value={controlId}
                onChange={(e) => { setControlId(e.target.value); setTargetStatements(new Set()); }}
                className="w-full h-10 px-3 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/30 focus:border-[var(--accent)]/40"
              >
                <option value="">Select control...</option>
                {controls.map((c) => (
                  <option key={c.control_id} value={c.control_id}>
                    {c.control_id} — {c.control_name}
                  </option>
                ))}
              </select>
              {selectedControl && (
                <p className="text-xs text-[var(--muted)] mt-1.5">
                  D statements: {selectedControl.d_statements.length} · E statements: {selectedControl.e_statements.length} · Domain: {selectedControl.domain}
                </p>
              )}
            </div>

            {/* Targeted D/E Statement Selector */}
            {selectedControl && (
              <div className="mb-4 p-4 bg-[var(--surface)] rounded-lg ring-1 ring-[var(--border)]">
                <div className="flex items-center justify-between mb-3">
                  <label className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider">
                    Target Specific D/E Statements
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        const all = new Set<string>();
                        selectedControl.d_statements.forEach((s) => all.add(s.id));
                        selectedControl.e_statements.forEach((s) => all.add(s.id));
                        setTargetStatements(all);
                      }}
                      className="text-[10px] text-[var(--accent)] hover:underline"
                    >
                      Select all
                    </button>
                    <button
                      onClick={() => setTargetStatements(new Set())}
                      className="text-[10px] text-[var(--muted)] hover:text-[var(--fg)] underline"
                    >
                      Clear
                    </button>
                  </div>
                </div>
                <p className="text-[10px] text-[var(--muted)]/70 mb-3">
                  Choose which D and E statement pair(s) your evidence addresses. If none selected, all statements are assessed.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-80 overflow-y-auto">
                  {/* Match D and E by number */}
                  {selectedControl.d_statements.map((ds, i) => {
                    const es = selectedControl.e_statements.find(
                      (e) => e.id.replace("E", "") === ds.id.replace("D", "")
                    );
                    const pairId = ds.id + (es ? ` + ${es.id}` : "");
                    const bothSelected = targetStatements.has(ds.id) && (es ? targetStatements.has(es.id) : true);
                    return (
                      <label
                        key={ds.id}
                        className={`flex items-start gap-2 p-2 rounded-md cursor-pointer transition-all border ${
                          bothSelected
                            ? "bg-[var(--accent)]/10 border-[var(--accent)]/30"
                            : "bg-[var(--surface-hover)]/50 border-transparent hover:border-[var(--border)]"
                        }`}
                      >
                        <input
                          type="checkbox"
                          className="mt-0.5 accent-[var(--accent)]"
                          checked={targetStatements.has(ds.id)}
                          onChange={(e) => {
                            const next = new Set(targetStatements);
                            if (e.target.checked) {
                              next.add(ds.id);
                              if (es) next.add(es.id);
                            } else {
                              next.delete(ds.id);
                              if (es) next.delete(es.id);
                            }
                            setTargetStatements(next);
                          }}
                        />
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-mono font-bold text-[var(--accent)]">
                            {pairId}
                          </span>
                          <span className="text-xs text-[var(--fg)]/70 ml-1.5 line-clamp-2">
                            {ds.text}
                          </span>
                          {es && (
                            <span className="text-xs text-purple-400/80 ml-1.5 line-clamp-2 block mt-0.5">
                              Evidence: {es.text}
                            </span>
                          )}
                        </div>
                      </label>
                    );
                  })}
                </div>
                {targetStatements.size > 0 && (
                  <p className="text-[10px] text-[var(--accent)] mt-2">
                    {targetStatements.size} statement(s) selected — assessment will target only these
                  </p>
                )}
              </div>
            )}

            {/* Samples in scope */}
            {selectedMarket && selectedControl && (
              <div className="mb-4 p-4 bg-[var(--surface)] rounded-lg ring-1 ring-[var(--border)]">
                <label className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider block mb-2">
                  Samples in Scope
                </label>
                <p className="text-[10px] text-[var(--muted)]/70 mb-3">
                  Add the specific samples being assessed (e.g., Phones, Tablets). These are saved per market + control and will be reused in future assessments until changed.
                </p>
                <SampleEditor
                  marketId={selectedMarket.id}
                  controlId={selectedControl.control_id}
                  tags={samples}
                  onChange={setSamples}
                />
              </div>
            )}

            {/* Statement type */}
            <div className="mb-4">
              <label className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider block mb-2">
                Statement Type
              </label>
              <div className="flex gap-2">
                {(["D", "E"] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setStatementType(t)}
                    className={`px-4 py-2 text-sm rounded-lg transition-all ${
                      statementType === t
                        ? "bg-[var(--accent)]/15 text-[var(--accent)] font-medium ring-1 ring-[var(--accent)]/20"
                        : "bg-[var(--surface)] text-[var(--muted)] ring-1 ring-[var(--border)] hover:text-[var(--fg)]"
                    }`}
                  >
                    {t === "D" ? "Design (D)" : "Evidence (E)"}
                  </button>
                ))}
              </div>
            </div>

            {/* Multi-file evidence upload */}
            <div className="mb-4">
              <label className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider block mb-2">
                Upload Evidence Files (optional — mix with text)
              </label>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragOver(false);
                  const dropped = Array.from(e.dataTransfer.files);
                  setEvidenceFiles((prev) => [...prev, ...dropped]);
                }}
                className={`border-2 border-dashed rounded-lg p-4 text-center transition-all cursor-pointer ${
                  dragOver
                    ? "border-[var(--accent)] bg-[var(--accent)]/5"
                    : "border-[var(--border)] hover:border-[var(--accent)]/40"
                }`}
                onClick={() => document.getElementById("multi-file-input")?.click()}
              >
                <input
                  id="multi-file-input"
                  type="file"
                  multiple
                  accept=".txt,.md,.pdf,.csv,.xlsx,.docx,.doc,.png,.jpg,.jpeg,.gif,.bmp"
                  className="hidden"
                  onChange={(e) => {
                    const chosen = Array.from(e.target.files || []);
                    setEvidenceFiles((prev) => [...prev, ...chosen]);
                    (e.target as HTMLInputElement).value = "";
                  }}
                />
                <FileUp className="w-5 h-5 mx-auto mb-1 text-[var(--muted)]" />
                <p className="text-xs text-[var(--muted)]">
                  Drag and drop files here, or <span className="text-[var(--accent)]">click to browse</span>
                </p>
                <p className="text-[10px] text-[var(--muted)]/60 mt-1">
                  .txt .md .pdf .csv .xlsx .docx .png .jpg — multiple files supported
                </p>
              </div>

              {/* File list */}
              {evidenceFiles.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  {evidenceFiles.map((f, i) => {
                    const ext = f.name.split(".").pop()?.toLowerCase() || "";
                    const colorMap: Record<string, string> = {
                      pdf: "text-red-400", docx: "text-blue-400", doc: "text-blue-400",
                      xlsx: "text-green-400", csv: "text-green-400",
                      png: "text-purple-400", jpg: "text-purple-400", jpeg: "text-purple-400",
                      txt: "text-[var(--muted)]", md: "text-[var(--muted)]",
                    };
                    return (
                      <div
                        key={`${f.name}-${i}`}
                        className="flex items-center gap-2 bg-[var(--surface-hover)] rounded-lg px-3 py-2 text-xs"
                      >
                        <span className={`font-mono font-bold uppercase ${colorMap[ext] || "text-[var(--muted)]"}`}>
                          {ext}
                        </span>
                        <span className="text-[var(--fg)] truncate flex-1">{f.name}</span>
                        <span className="text-[var(--muted)] tabular-nums">{(f.size / 1024).toFixed(1)} KB</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEvidenceFiles((prev) => prev.filter((_, j) => j !== i));
                          }}
                          className="text-[var(--muted)] hover:text-[var(--fail)] ml-1"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })}
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-[10px] text-[var(--muted)]">
                      {evidenceFiles.length} file{evidenceFiles.length > 1 ? "s" : ""} —{" "}
                      {(evidenceFiles.reduce((s, f) => s + f.size, 0) / 1024).toFixed(1)} KB total
                    </span>
                    <button
                      onClick={() => setEvidenceFiles([])}
                      className="text-[10px] text-[var(--muted)] hover:text-[var(--fail)] underline"
                    >
                      Clear all
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Evidence text */}
            <div className="mb-4">
              <label className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider block mb-2">
                Evidence Text
              </label>
              <textarea
                value={evidenceText}
                onChange={(e) => setEvidenceText(e.target.value)}
                rows={8}
                placeholder="Paste audit evidence here... e.g., policy documents, access reviews, configuration exports..."
                className="w-full px-4 py-3 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] placeholder:text-[var(--muted)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/30 focus:border-[var(--accent)]/40 resize-y font-mono"
              />
            </div>

            {/* Run */}
            <button
              onClick={runSingleAssess}
              disabled={loading || !controlId || (!evidenceText.trim() && evidenceFiles.length === 0)}
              className="flex items-center gap-2 px-5 py-2.5 bg-[var(--accent)] text-white text-sm font-medium rounded-lg hover:bg-[var(--accent)]/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analysing...
                </>
              ) : (
                <>
                  <ClipboardCheck className="w-4 h-4" />
                  Run Assessment
                </>
              )}
            </button>
          </div>

          {/* Error */}
          {error && (
            <div className="glass p-4 ring-1 ring-[var(--fail)]/20">
              <div className="flex items-center gap-2 text-[var(--fail)]">
                <XCircle className="w-4 h-4" />
                <span className="text-sm font-medium">{error}</span>
              </div>
            </div>
          )}

          {/* Single Result */}
          {result && <ResultCard result={result} />}
        </div>
      )}

      {/* Batch Assessment */}
      {activeTab === "batch" && (
        <div className="space-y-6">
          {/* Add item form */}
          <div className="glass p-6">
            <h2 className="text-sm font-semibold text-[var(--fg)] mb-4">Add Assessment Item</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
              <select
                value={batchControlId}
                onChange={(e) => setBatchControlId(e.target.value)}
                className="h-10 px-3 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/30"
              >
                <option value="">Select control...</option>
                {controls.map((c) => (
                  <option key={c.control_id} value={c.control_id}>
                    {c.control_id}
                  </option>
                ))}
              </select>
              <textarea
                value={batchEvidence}
                onChange={(e) => setBatchEvidence(e.target.value)}
                rows={1}
                placeholder="Evidence text..."
                className="md:col-span-2 px-3 py-2 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] placeholder:text-[var(--muted)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/30 resize-none font-mono"
              />
              <button
                onClick={addBatchItem}
                disabled={!batchControlId || !batchEvidence.trim()}
                className="h-10 px-4 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] hover:border-[var(--accent)]/40 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                <FileUp className="w-4 h-4 inline mr-1" />
                Add
              </button>
            </div>

            {/* Batch items list */}
            {batchItems.length > 0 && (
              <>
                <div className="border-t border-[var(--border)] pt-4 mb-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider">
                      {batchItems.length} items in batch
                    </span>
                    <button
                      onClick={() => setBatchItems([])}
                      className="flex items-center gap-1 text-xs text-[var(--muted)] hover:text-[var(--fail)] transition-colors"
                    >
                      <Trash className="w-3 h-3" /> Clear all
                    </button>
                  </div>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {batchItems.map((item, i) => (
                      <div key={i} className="flex items-center gap-3 bg-[var(--surface-hover)] rounded-lg px-3 py-2">
                        <span className="font-mono text-xs text-[var(--accent)]">{item.control_id}</span>
                        <span className="flex-1 text-xs text-[var(--muted)] truncate">{item.evidence_text}</span>
                        <button
                          onClick={() => removeBatchItem(i)}
                          className="text-[var(--muted)] hover:text-[var(--fail)] transition-colors"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  onClick={runBatchAssess}
                  disabled={loading}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[var(--accent)] text-white text-sm font-medium rounded-lg hover:bg-[var(--accent)]/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Running {batchItems.length} assessments...
                    </>
                  ) : (
                    <>
                      <ClipboardCheck className="w-4 h-4" />
                      Run Batch ({batchItems.length})
                    </>
                  )}
                </button>
              </>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="glass p-4 ring-1 ring-[var(--fail)]/20">
              <div className="flex items-center gap-2 text-[var(--fail)]">
                <XCircle className="w-4 h-4" />
                <span className="text-sm font-medium">{error}</span>
              </div>
            </div>
          )}

          {/* Batch results */}
          {batchResults.length > 0 && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="glass p-5">
                <h2 className="text-sm font-semibold text-[var(--fg)] mb-4">Batch Summary</h2>
                <div className="grid grid-cols-4 gap-3">
                  {(["PASS", "PARTIAL", "FAIL", "INSUFFICIENT_EVIDENCE"] as const).map((v) => {
                    const count = verdictSummary[v];
                    const config = {
                      PASS: { icon: CheckCircle, className: "text-[var(--pass)]" },
                      PARTIAL: { icon: AlertTriangle, className: "text-[var(--partial)]" },
                      FAIL: { icon: XCircle, className: "text-[var(--fail)]" },
                      INSUFFICIENT_EVIDENCE: { icon: ShieldAlert, className: "text-[var(--insufficient)]" },
                    };
                    const { icon: Icon, className } = config[v];
                    return (
                      <div key={v} className="text-center">
                        <Icon className={`w-5 h-5 mx-auto mb-1 ${className}`} />
                        <p className="text-2xl font-bold tabular-nums">{count}</p>
                        <p className="text-[10px] text-[var(--muted)]">{v.replace("_", " ")}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Individual results */}
              <div className="space-y-4">
                {batchResults.map((r, i) => (
                  <ResultCard key={i} result={r} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* XLSX Upload Tab */}
      {activeTab === "xlsx" && (
        <div className="space-y-6">
          <div className="glass p-6">
            <h2 className="text-sm font-semibold text-[var(--fg)] mb-2">Upload XLSX Spreadsheet</h2>
            <p className="text-xs text-[var(--muted)] mb-4">
              Upload an Excel file with columns: <code className="font-mono text-[var(--accent)]">control_id</code>,{" "}
              <code className="font-mono text-[var(--accent)]">evidence_text</code>, and optionally{" "}
              <code className="font-mono text-[var(--accent)]">statement_type</code> (D or E). Each row is assessed against
              the corresponding control.
            </p>

            {/* Drag/drop area */}
            <div
              onDragOver={(e) => { e.preventDefault(); setXlsxDrag(true); }}
              onDragLeave={() => setXlsxDrag(false)}
              onDrop={(e) => {
                e.preventDefault();
                setXlsxDrag(false);
                const f = e.dataTransfer.files[0];
                if (f && f.name.endsWith(".xlsx")) setXlsxFile(f);
              }}
              className={`border-2 border-dashed rounded-xl p-10 text-center transition-all cursor-pointer ${
                xlsxDrag
                  ? "border-[var(--accent)] bg-[var(--accent)]/5"
                  : xlsxFile
                  ? "border-[var(--pass)] bg-[var(--pass)]/5"
                  : "border-[var(--border)] hover:border-[var(--accent)]/40"
              }`}
              onClick={() => document.getElementById("xlsx-input")?.click()}
            >
              <input
                id="xlsx-input"
                type="file"
                accept=".xlsx"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) setXlsxFile(f);
                }}
              />
              {xlsxFile ? (
                <div>
                  <FileUp className="w-10 h-10 mx-auto mb-3 text-[var(--pass)]" />
                  <p className="text-sm font-medium text-[var(--fg)]">{xlsxFile.name}</p>
                  <p className="text-xs text-[var(--muted)] mt-1">
                    {(xlsxFile.size / 1024).toFixed(1)} KB
                  </p>
                  <button
                    onClick={(e) => { e.stopPropagation(); setXlsxFile(null); }}
                    className="mt-3 text-xs text-[var(--muted)] hover:text-[var(--fail)] underline"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div>
                  <FileUp className="w-10 h-10 mx-auto mb-3 text-[var(--muted)]" />
                  <p className="text-sm text-[var(--muted)]">
                    Drag and drop an <span className="text-[var(--fg)] font-medium">.xlsx</span> file here
                  </p>
                  <p className="text-xs text-[var(--muted)]/60 mt-1">or click to browse</p>
                </div>
              )}
            </div>

            {/* Sample format */}
            <details className="mt-4">
              <summary className="text-xs text-[var(--muted)] cursor-pointer hover:text-[var(--fg)]">
                View expected XLSX format
              </summary>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border)]">
                      <th className="text-left py-2 px-3 text-[var(--accent)] font-mono">control_id</th>
                      <th className="text-left py-2 px-3 text-[var(--accent)] font-mono">evidence_text</th>
                      <th className="text-left py-2 px-3 text-[var(--accent)] font-mono">statement_type</th>
                    </tr>
                  </thead>
                  <tbody className="text-[var(--muted)] font-mono">
                    <tr className="border-b border-[var(--border)]/50">
                      <td className="py-2 px-3">IAM_001</td>
                      <td className="py-2 px-3">User access review procedure approved 2025-11-01...</td>
                      <td className="py-2 px-3">D</td>
                    </tr>
                    <tr className="border-b border-[var(--border)]/50">
                      <td className="py-2 px-3">IAM_002</td>
                      <td className="py-2 px-3">Privileged access quarterly review completed on...</td>
                      <td className="py-2 px-3">E</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3">NET_001</td>
                      <td className="py-2 px-3">Network segmentation firewall rules last reviewed...</td>
                      <td className="py-2 px-3">D</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </details>

            {/* Upload & run */}
            {xlsxFile && (
              <button
                onClick={runXlsxAssess}
                disabled={loading}
                className="flex items-center gap-2 mt-5 px-5 py-2.5 bg-[var(--accent)] text-white text-sm font-medium rounded-lg hover:bg-[var(--accent)]/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing XLSX...
                  </>
                ) : (
                  <>
                    <ClipboardCheck className="w-4 h-4" />
                    Assess All from XLSX
                  </>
                )}
              </button>
            )}
          </div>

          {/* XLSX Error */}
          {error && activeTab === "xlsx" && (
            <div className="glass p-4 ring-1 ring-[var(--fail)]/20">
              <div className="flex items-center gap-2 text-[var(--fail)]">
                <XCircle className="w-4 h-4" />
                <span className="text-sm font-medium">{error}</span>
              </div>
            </div>
          )}

          {/* XLSX Results */}
          {batchResults.length > 0 && activeTab === "xlsx" && (
            <div className="space-y-6">
              <div className="glass p-5">
                <h2 className="text-sm font-semibold text-[var(--fg)] mb-4">XLSX Assessment Results</h2>
                <div className="grid grid-cols-4 gap-3">
                  {(["PASS", "PARTIAL", "FAIL", "INSUFFICIENT_EVIDENCE"] as const).map((v) => {
                    const count = verdictSummary[v];
                    const cfg = {
                      PASS: { icon: CheckCircle, className: "text-[var(--pass)]" },
                      PARTIAL: { icon: AlertTriangle, className: "text-[var(--partial)]" },
                      FAIL: { icon: XCircle, className: "text-[var(--fail)]" },
                      INSUFFICIENT_EVIDENCE: { icon: ShieldAlert, className: "text-[var(--insufficient)]" },
                    };
                    const { icon: Icon, className } = cfg[v];
                    return (
                      <div key={v} className="text-center">
                        <Icon className={`w-5 h-5 mx-auto mb-1 ${className}`} />
                        <p className="text-2xl font-bold tabular-nums">{count}</p>
                        <p className="text-[10px] text-[var(--muted)]">{v.replace("_", " ")}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
              <div className="space-y-4">
                {batchResults.map((r, i) => (
                  <ResultCard key={i} result={r} />
                ))}
              </div>
            </div>
          )}

          {/* Loading for XLSX */}
          {loading && activeTab === "xlsx" && (
            <div className="glass p-12 text-center">
              <Loader2 className="w-8 h-8 mx-auto mb-4 text-[var(--accent)] animate-spin" />
              <p className="text-sm text-[var(--muted)]">Processing XLSX and running assessments with Claude...</p>
              <p className="text-xs text-[var(--muted)]/60 mt-1">This may take a moment depending on row count</p>
            </div>
          )}
        </div>
      )}

      {/* Loading overlay for batch */}
      {loading && activeTab === "batch" && batchItems.length > 0 && (
        <div className="glass p-12 text-center mt-6">
          <Loader2 className="w-8 h-8 mx-auto mb-4 text-[var(--accent)] animate-spin" />
          <p className="text-sm text-[var(--muted)]">Running assessments with Claude...</p>
          <p className="text-xs text-[var(--muted)]/60 mt-1">This may take a moment for large batches</p>
        </div>
      )}
    </motion.div>
  );
}

function ResultCard({ result }: { result: AssessmentResult }) {
  const [pdfLoading, setPdfLoading] = useState(false);

  const handleDownloadPdf = async () => {
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
    } catch (e) {
      console.error("PDF download failed", e);
    } finally {
      setPdfLoading(false);
    }
  };

  const verdictIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    PASS: CheckCircle,
    PARTIAL: AlertTriangle,
    FAIL: XCircle,
    INSUFFICIENT_EVIDENCE: ShieldAlert,
  };
  const verdictColors: Record<string, string> = {
    PASS: "var(--pass)",
    PARTIAL: "var(--partial)",
    FAIL: "var(--fail)",
    INSUFFICIENT_EVIDENCE: "var(--insufficient)",
  };
  const Icon = verdictIcons[result.verdict] ?? ShieldAlert;

  const strengthColors: Record<string, string> = {
    STRONG: "text-[var(--pass)]",
    MODERATE: "text-[var(--partial)]",
    WEAK: "text-[var(--fail)]",
    NIL: "text-[var(--insufficient)]",
  };

  const statusIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    MET: CheckCircle,
    PARTIALLY_MET: AlertTriangle,
    NOT_MET: XCircle,
  };

  return (
    <div className="glass p-6 space-y-6">
      {/* === HEADER === */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
            style={{ backgroundColor: `${verdictColors[result.verdict]}15` }}
          >
            <span style={{ color: verdictColors[result.verdict] }}>
              <Icon className="w-5 h-5" />
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-[var(--fg)]">{result.control_name}</span>
              <VerdictBadge verdict={result.verdict} />
              <RiskBadge rating={result.risk_rating} />
              {result.compliance_status && (
                <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold ring-1 ${
                  result.compliance_status === "FULL" ? "bg-[var(--pass)]/10 text-[var(--pass)] ring-[var(--pass)]/20" :
                  result.compliance_status === "PARTIAL" ? "bg-[var(--partial)]/10 text-[var(--partial)] ring-[var(--partial)]/20" :
                  result.compliance_status === "NON-COMPLIANT" ? "bg-[var(--fail)]/10 text-[var(--fail)] ring-[var(--fail)]/20" :
                  "bg-[var(--insufficient)]/10 text-[var(--insufficient)] ring-[var(--insufficient)]/20"
                }`}>
                  {result.compliance_status}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="font-mono text-[10px] text-[var(--muted)]">{result.control_id}</span>
              <span className="text-[10px] text-[var(--muted)]">·</span>
              <span className="text-[10px] text-[var(--muted)]">{result.statement_type === "D" ? "Design Assessment" : "Evidence Assessment"}</span>
              <span className="text-[10px] text-[var(--muted)]">·</span>
              <span className="font-mono text-[10px] text-[var(--muted)]">{Math.round(result.confidence * 100)}% confidence</span>
              <span className="text-[10px] text-[var(--muted)]">·</span>
              <span className="text-[10px] text-[var(--muted)]">{result.tokens_used?.toLocaleString()} tokens</span>
            </div>
          </div>
        </div>
        <button
          onClick={handleDownloadPdf}
          disabled={pdfLoading}
          className="shrink-0 inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium bg-[var(--accent)]/10 hover:bg-[var(--accent)]/20 text-[var(--accent)] ring-1 ring-[var(--accent)]/20 transition-all duration-200 disabled:opacity-50"
        >
          {pdfLoading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Download className="w-3.5 h-3.5" />
          )}
          Export PDF
        </button>
      </div>

      {/* === AUDIT OPINION (Executive Summary) === */}
      {result.audit_opinion && (
        <div className="p-4 bg-[var(--accent)]/5 rounded-lg ring-1 ring-[var(--accent)]/10 border-l-2 border-[var(--accent)]">
          <h3 className="text-xs font-semibold text-[var(--accent)] uppercase tracking-wider mb-2">Audit Opinion</h3>
          <p className="text-sm text-[var(--fg)]/90 leading-relaxed">{result.audit_opinion}</p>
        </div>
      )}

      {/* === METHODOLOGY === */}
      {result.assessment_methodology && (
        <div>
          <h3 className="text-xs font-semibold text-[var(--fg)] uppercase tracking-wider mb-1">Assessment Methodology</h3>
          <p className="text-xs text-[var(--muted)] leading-relaxed">{result.assessment_methodology}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* === REQUIREMENT ASSESSMENT TABLE === */}
        {result.requirement_assessment?.length > 0 && (
          <div className="lg:col-span-2">
            <h3 className="text-xs font-semibold text-[var(--fg)] uppercase tracking-wider mb-2">Requirement-by-Requirement Assessment</h3>
            <div className="overflow-x-auto rounded-lg ring-1 ring-[var(--border)]">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--surface-hover)]">
                    <th className="text-left py-2.5 px-3 text-[var(--muted)] font-semibold uppercase tracking-wider w-16">ID</th>
                    <th className="text-left py-2.5 px-3 text-[var(--muted)] font-semibold uppercase tracking-wider w-24">Status</th>
                    <th className="text-left py-2.5 px-3 text-[var(--muted)] font-semibold uppercase tracking-wider">Assessment Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {result.requirement_assessment.map((ra, i) => {
                    const SIcon = statusIcons[ra.status];
                    const statusColor =
                      ra.status === "MET" ? "text-[var(--pass)]" :
                      ra.status === "PARTIALLY_MET" ? "text-[var(--partial)]" :
                      "text-[var(--fail)]";
                    return (
                      <tr key={i} className="border-b border-[var(--border)]/50 hover:bg-[var(--surface-hover)]/50 transition-colors">
                        <td className="py-2.5 px-3 font-mono text-[var(--accent)] font-bold align-top">{ra.statement_id}</td>
                        <td className="py-2.5 px-3 align-top">
                          <span className={`inline-flex items-center gap-1 ${statusColor}`}>
                            {SIcon && <SIcon className="w-3 h-3" />}
                            <span className="text-[10px] font-semibold">{ra.status.replace("_", " ")}</span>
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-[var(--fg)]/80 leading-relaxed">{ra.assessment_detail}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* === EVIDENCE INVENTORY === */}
        {result.evidence_inventory?.length > 0 && (
          <div className="lg:col-span-2">
            <h3 className="text-xs font-semibold text-[var(--fg)] uppercase tracking-wider mb-2">Evidence Inventory</h3>
            <div className="overflow-x-auto rounded-lg ring-1 ring-[var(--border)]">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--surface-hover)]">
                    <th className="text-left py-2 px-3 text-[var(--muted)] font-semibold uppercase">Source</th>
                    <th className="text-left py-2 px-3 text-[var(--muted)] font-semibold uppercase">Type</th>
                    <th className="text-left py-2 px-3 text-[var(--muted)] font-semibold uppercase">Date</th>
                    <th className="text-left py-2 px-3 text-[var(--muted)] font-semibold uppercase">Strength</th>
                    <th className="text-left py-2 px-3 text-[var(--muted)] font-semibold uppercase">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {result.evidence_inventory.map((ei, i) => (
                    <tr key={i} className="border-b border-[var(--border)]/50">
                      <td className="py-2 px-3 text-[var(--accent)] font-mono">{ei.file}</td>
                      <td className="py-2 px-3 text-[var(--muted)]">{ei.type}</td>
                      <td className="py-2 px-3 text-[var(--muted)]">{ei.date_observed || "—"}</td>
                      <td className={`py-2 px-3 font-semibold ${strengthColors[ei.strength_rating] || "text-[var(--muted)]"}`}>{ei.strength_rating}</td>
                      <td className="py-2 px-3 text-[var(--fg)]/80">{ei.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* === JUSTIFICATION === */}
      {result.justification && (
        <div className="p-4 bg-[var(--surface-hover)] rounded-lg ring-1 ring-[var(--border)]">
          <h3 className="text-xs font-semibold text-[var(--fg)] uppercase tracking-wider mb-2">Detailed Justification</h3>
          <p className="text-sm text-[var(--fg)]/85 leading-relaxed whitespace-pre-line">{result.justification}</p>
        </div>
      )}

      {/* === SATISFIED vs GAPS side by side === */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {result.satisfied_requirements.length > 0 && (
          <div className="p-4 bg-[var(--pass)]/5 rounded-lg ring-1 ring-[var(--pass)]/10">
            <h3 className="text-xs font-semibold text-[var(--pass)] mb-2 font-mono uppercase">Satisfied Requirements ({result.satisfied_requirements.length})</h3>
            <ul className="space-y-1.5">
              {result.satisfied_requirements.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-[var(--fg)]/80">
                  <span className="text-[var(--pass)] mt-1 flex-shrink-0">&#10003;</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {result.gaps.length > 0 && (
          <div className="p-4 bg-[var(--fail)]/5 rounded-lg ring-1 ring-[var(--fail)]/10 md:col-span-1">
            <h3 className="text-xs font-semibold text-[var(--fail)] mb-2 font-mono uppercase">Gaps ({result.gaps.length})</h3>
            <ul className="space-y-1.5">
              {result.gaps.map((g, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-[var(--fg)]/80">
                  <span className="text-[var(--fail)] mt-1 flex-shrink-0">&#10007;</span>
                  <span>{g}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* === LIMITATIONS === */}
      {result.limitations?.length > 0 && (
        <div className="p-4 bg-amber-500/5 rounded-lg ring-1 ring-amber-500/10 border-l-2 border-amber-500/30">
          <h3 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">Assessment Limitations</h3>
          <ul className="space-y-1">
            {result.limitations.map((l, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[var(--fg)]/70">
                <span className="text-amber-400 mt-0.5 flex-shrink-0">!</span>
                <span>{l}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* === DRAFT FINDING === */}
      {result.draft_finding && (
        <div className="p-4 bg-[var(--surface-hover)] rounded-lg ring-1 ring-[var(--border)] border-l-2 border-[var(--partial)]">
          <h3 className="text-xs font-semibold text-[var(--fg)] uppercase tracking-wider mb-3">Audit Finding: {result.draft_finding.title}</h3>
          <div className="space-y-3 text-sm">
            <FindingRow label="Observation" text={result.draft_finding.observation} />
            <FindingRow label="Criteria" text={result.draft_finding.criteria} />
            <FindingRow label="Risk Impact" text={result.draft_finding.risk_impact} />
            <FindingRow label="Recommendation" text={result.draft_finding.recommendation} />
            {result.draft_finding.management_action && (
              <FindingRow label="Management Action Required" text={result.draft_finding.management_action} />
            )}
          </div>
        </div>
      )}

      {/* === FOLLOW-UP QUESTIONS === */}
      {result.follow_up_questions?.length > 0 && (
        <div className="p-4 bg-[var(--accent)]/5 rounded-lg ring-1 ring-[var(--accent)]/10 border-l-2 border-[var(--accent)]/30">
          <h3 className="text-xs font-semibold text-[var(--accent)] uppercase tracking-wider mb-2">Follow-up Questions for Control Owner</h3>
          <ol className="space-y-1.5 list-decimal list-inside">
            {result.follow_up_questions.map((q, i) => (
              <li key={i} className="text-sm text-[var(--fg)]/80 pl-1">{q}</li>
            ))}
          </ol>
        </div>
      )}

      {/* === RECOMMENDED EVIDENCE === */}
      {result.recommended_evidence?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-[var(--fg)] uppercase tracking-wider mb-2">Recommended Evidence to Collect</h3>
          <ul className="space-y-1">
            {result.recommended_evidence.map((re, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[var(--muted)]">
                <span className="text-[var(--accent)] mt-0.5">&#9656;</span>
                {re}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* === REMEDIATION NOTES === */}
      {result.remediation_notes && (
        <div className="p-4 bg-[var(--surface-hover)] rounded-lg ring-1 ring-[var(--border)]">
          <h3 className="text-xs font-semibold text-[var(--fg)] uppercase tracking-wider mb-2">Remediation Guidance</h3>
          <p className="text-sm text-[var(--muted)] leading-relaxed whitespace-pre-line">{result.remediation_notes}</p>
        </div>
      )}
    </div>
  );
}

function FindingRow({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <span className="text-xs text-[var(--muted)] font-medium">{label}</span>
      <p className="text-[var(--fg)]/85 mt-0.5">{text}</p>
    </div>
  );
}

export default function AssessPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-5xl mx-auto px-6 py-8">
          <div className="glass p-12 text-center">
            <div className="w-8 h-8 mx-auto mb-4 border-2 border-[var(--accent)]/30 border-t-[var(--accent)] rounded-full animate-spin" />
            <p className="text-sm text-[var(--muted)]">Loading...</p>
          </div>
        </div>
      }
    >
      <AssessContent />
    </Suspense>
  );
}
