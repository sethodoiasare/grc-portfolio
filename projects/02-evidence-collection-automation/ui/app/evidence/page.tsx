"use client";

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Layers, Search, Trash2, X, ChevronDown, ChevronRight, MapPin } from "lucide-react";
import { useAuth } from "../_hooks/useAuth";

interface EvidenceItem {
  id: number; evidence_type: string; source_system: string;
  data: Record<string, unknown>; freshness_date: string; control_mapping: string[];
  connector_name: string; market_id: number | null;
}

export default function EvidencePage() {
  const [items, setItems] = useState<EvidenceItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    fetch("/api/v1/evidence?limit=200", { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setItems).catch(() => {}).finally(() => setLoading(false));
  }, [token]);

  const filtered = useMemo(() => {
    if (!search.trim()) return items;
    const q = search.toLowerCase();
    return items.filter(i =>
      i.evidence_type.toLowerCase().includes(q) ||
      i.source_system.toLowerCase().includes(q) ||
      i.connector_name?.toLowerCase().includes(q) ||
      i.control_mapping?.some(c => c.toLowerCase().includes(q))
    );
  }, [items, search]);

  async function deleteItem(id: number) {
    await fetch(`/api/v1/evidence/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
    setItems(prev => prev.filter(i => i.id !== id));
  }

  const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.03 } } };
  const cardItem = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 400, damping: 30 } } };

  return (
    <motion.div className="max-w-6xl mx-auto px-6 py-10" variants={container} initial="hidden" animate="show">
      <motion.div variants={cardItem} className="mb-8">
        <motion.div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-4"
          style={{ background: "rgba(91, 141, 239, 0.08)", color: "var(--accent)", border: "1px solid rgba(91, 141, 239, 0.15)" }}>
          <Layers className="w-3 h-3" /> Evidence Library
        </motion.div>
        <h1 className="text-4xl font-bold tracking-[-0.03em] text-[var(--fg)]">Evidence Items</h1>
        <p className="text-sm text-[var(--muted)] mt-2">{items.length} items collected across all connectors</p>
      </motion.div>

      <motion.div variants={cardItem} className="mb-6 relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)] w-4 h-4" />
        <input type="text" placeholder="Search by type, source, or control..." value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full pl-9 pr-4 py-2.5 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] placeholder:text-[var(--muted)]/50 outline-none focus:border-[var(--accent)]" />
        {search && <button onClick={() => setSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"><X size={14} /></button>}
      </motion.div>

      <div className="space-y-2">
        {loading ? [1,2,3].map(i => <div key={i} className="glass p-4"><div className="skeleton w-48 h-4 rounded" /></div>) : (
          filtered.length === 0 ? (
            <div className="text-center py-20"><Layers size={40} className="mx-auto mb-4 text-[var(--muted)]/30" /><p className="text-sm text-[var(--muted)]">No evidence items found.</p></div>
          ) : (
            filtered.map(i => (
              <motion.div key={i.id} variants={cardItem} className="glass overflow-hidden">
                <button onClick={() => setExpanded(expanded === i.id ? null : i.id)}
                  className="w-full p-4 flex items-center gap-4 text-left hover:bg-[var(--surface-hover)]/50 transition-colors">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-[var(--fg)] capitalize">{i.evidence_type.replace(/_/g, " ")}</p>
                    <p className="text-xs text-[var(--muted)]">{i.source_system} · {i.connector_name} · {new Date(i.freshness_date).toLocaleDateString()}</p>
                  </div>
                  {i.control_mapping?.length > 0 && (
                    <div className="flex gap-1 flex-wrap">{i.control_mapping.slice(0, 3).map(c => <span key={c} className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--accent)]/10 text-[var(--accent)]">{c}</span>)}</div>
                  )}
                  <button onClick={(e) => { e.stopPropagation(); deleteItem(i.id); }} className="text-[var(--muted)] hover:text-[var(--fail)] p-1"><Trash2 size={14} /></button>
                  <motion.div animate={{ rotate: expanded === i.id ? 180 : 0 }}><ChevronDown size={16} className="text-[var(--muted)]" /></motion.div>
                </button>
                {expanded === i.id && (
                  <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} className="overflow-hidden border-t border-[var(--border)]">
                    <pre className="p-4 text-xs text-[var(--muted)] overflow-x-auto whitespace-pre-wrap font-mono">{JSON.stringify(i.data, null, 2)}</pre>
                  </motion.div>
                )}
              </motion.div>
            ))
          )
        )}
      </div>
    </motion.div>
  );
}
