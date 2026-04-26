"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Package, Plus, Download, Send, CheckCircle, Loader2 } from "lucide-react";
import { useAuth } from "../_hooks/useAuth";

interface Bundle {
  id: number; name: string; description: string; item_ids: number[];
  control_ids: string[]; created_at: string; market_name: string | null;
}

interface EvidenceItem {
  id: number; evidence_type: string; source_system: string;
}

export default function BundlesPage() {
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [bundleName, setBundleName] = useState("");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [status, setStatus] = useState<string | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    Promise.all([
      fetch("/api/v1/bundles", { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
      fetch("/api/v1/evidence?limit=100", { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
    ]).then(([b, e]) => { setBundles(b); setEvidence(e); }).catch(() => {}).finally(() => setLoading(false));
  }, [token]);

  async function createBundle() {
    if (!bundleName.trim() || selected.size === 0) return;
    setCreating(true);
    const res = await fetch("/api/v1/bundles", {
      method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ name: bundleName, item_ids: [...selected], description: "" }),
    });
    if (res.ok) {
      const b = await res.json();
      setBundles(prev => [b, ...prev]);
      setBundleName(""); setSelected(new Set());
    }
    setCreating(false);
  }

  async function downloadBundle(id: number) {
    const res = await fetch(`/api/v1/bundles/${id}/download`, { headers: { Authorization: `Bearer ${token}` } });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `bundle_${id}.json`; a.click();
    URL.revokeObjectURL(url);
  }

  async function sendToAnalyser(id: number) {
    setStatus(`assess-${id}`);
    const res = await fetch(`/api/v1/bundles/${id}/assess`, {
      method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    setStatus(null);
    if (data.status === "ready_to_assess") {
      // Try to POST to Project 1 if running
      try {
        const p1Res = await fetch("http://localhost:8001/api/v1/assess/batch", {
          method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify(data.payload),
        });
        if (p1Res.ok) alert(`Sent to ITGC Analyser! ${data.assessment_count} assessments queued.`);
        else alert(`Bundle ready. P1 responded: ${p1Res.status}`);
      } catch {
        alert(`Bundle ready! ${data.assessment_count} assessments prepared. Start P1 to run assessment.`);
      }
    }
  }

  const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.04 } } };
  const cardItem = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 400, damping: 30 } } };

  return (
    <motion.div className="max-w-6xl mx-auto px-6 py-10" variants={container} initial="hidden" animate="show">
      <motion.div variants={cardItem} className="mb-8">
        <motion.div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-4"
          style={{ background: "rgba(91, 141, 239, 0.08)", color: "var(--accent)", border: "1px solid rgba(91, 141, 239, 0.15)" }}>
          <Package className="w-3 h-3" /> Bundles
        </motion.div>
        <h1 className="text-4xl font-bold tracking-[-0.03em] text-[var(--fg)]">Evidence Bundles</h1>
        <p className="text-sm text-[var(--muted)] mt-2">Group evidence items and send to the ITGC Evidence Analyser for assessment.</p>
      </motion.div>

      {/* Create bundle */}
      <motion.div variants={cardItem} className="glass p-6 mb-8">
        <h2 className="text-sm font-semibold text-[var(--fg)] mb-3">Create New Bundle</h2>
        <div className="flex gap-3 mb-3">
          <input type="text" placeholder="Bundle name..." value={bundleName}
            onChange={e => setBundleName(e.target.value)}
            className="flex-1 px-3 py-2 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] outline-none focus:border-[var(--accent)]" />
          <button onClick={createBundle} disabled={creating || !bundleName || selected.size === 0}
            className="flex items-center gap-1.5 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-semibold disabled:opacity-40">
            {creating ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} Create
          </button>
        </div>
        <p className="text-xs text-[var(--muted)] mb-2">{selected.size} items selected</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 max-h-40 overflow-y-auto">
          {evidence.slice(0, 50).map((e) => (
            <label key={e.id} className={`flex items-center gap-2 p-2 rounded text-xs cursor-pointer border ${
              selected.has(e.id) ? "bg-[var(--accent)]/10 border-[var(--accent)]/30" : "bg-[var(--surface-hover)]/50 border-transparent hover:border-[var(--border)]"
            }`}>
              <input type="checkbox" checked={selected.has(e.id)} onChange={() => {
                const next = new Set(selected);
                next.has(e.id) ? next.delete(e.id) : next.add(e.id);
                setSelected(next);
              }} className="accent-[var(--accent)]" />
              <span className="text-[var(--fg)] truncate">{e.evidence_type.replace(/_/g, " ")}</span>
            </label>
          ))}
        </div>
      </motion.div>

      {/* Existing bundles */}
      <div className="space-y-3">
        {loading ? [1,2].map(i => <div key={i} className="glass p-5"><div className="skeleton w-48 h-4 rounded" /></div>) : (
          bundles.length === 0 ? (
            <div className="text-center py-20"><Package size={40} className="mx-auto mb-4 text-[var(--muted)]/30" /><p className="text-sm text-[var(--muted)]">No bundles yet.</p></div>
          ) : (
            bundles.map(b => (
              <motion.div key={b.id} variants={cardItem} className="glass p-5 flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: "rgba(91,141,239,0.1)" }}>
                  <Package size={18} color="var(--accent)" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-[var(--fg)]">{b.name}</p>
                  <p className="text-xs text-[var(--muted)]">{b.item_ids.length} items · {b.control_ids.length} controls · {new Date(b.created_at).toLocaleDateString()}</p>
                </div>
                <button onClick={() => downloadBundle(b.id)} className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-[var(--accent)]/10 text-[var(--accent)] hover:bg-[var(--accent)]/20">
                  <Download size={12} /> Export
                </button>
                <button onClick={() => sendToAnalyser(b.id)} disabled={status === `assess-${b.id}`}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-[var(--pass)]/10 text-[var(--pass)] hover:bg-[var(--pass)]/20 disabled:opacity-50">
                  {status === `assess-${b.id}` ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
                  Assess
                </button>
              </motion.div>
            ))
          )
        )}
      </div>
    </motion.div>
  );
}
