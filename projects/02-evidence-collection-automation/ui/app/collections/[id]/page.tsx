"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { Database, CheckCircle, Loader2, Calendar, MapPin, Layers, ChevronDown, ChevronRight } from "lucide-react";
import { useAuth } from "../../_hooks/useAuth";

interface EvidenceItem {
  id: number; evidence_type: string; source_system: string;
  data: Record<string, unknown>; freshness_date: string; control_mapping: string[];
}
interface Collection {
  id: number; connector_name: string; market_name: string | null;
  status: string; started_at: string; completed_at: string | null;
  evidence_count: number; control_ids: string[];
  evidence_items: EvidenceItem[];
}

export default function CollectionDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const [collection, setCollection] = useState<Collection | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    fetch(`/api/v1/collections/${id}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setCollection).catch(() => {}).finally(() => setLoading(false));
  }, [id, token]);

  if (loading) {
    return <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="glass p-5"><div className="skeleton w-64 h-6 rounded mb-2" /><div className="skeleton w-32 h-4 rounded" /></div>
    </div>;
  }
  if (!collection) {
    return <div className="max-w-4xl mx-auto px-6 py-10 text-center py-20">
      <Database size={40} className="mx-auto mb-4 text-[var(--muted)]/30" />
      <p className="text-sm text-[var(--muted)]">Collection not found.</p>
    </div>;
  }

  return (
    <motion.div className="max-w-4xl mx-auto px-6 py-10" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--fg)]">{collection.connector_name}</h1>
        <div className="flex items-center gap-3 mt-2 text-xs text-[var(--muted)]">
          <span className="flex items-center gap-1"><Calendar size={12} />{new Date(collection.started_at).toLocaleString()}</span>
          {collection.market_name && <span className="flex items-center gap-1"><MapPin size={12} />{collection.market_name}</span>}
          <span className="flex items-center gap-1"><Layers size={12} />{collection.evidence_count} items</span>
          <span className={`px-2 py-0.5 rounded-full text-xs ${collection.status === "complete" ? "bg-[var(--pass)]/10 text-[var(--pass)]" : "bg-[var(--partial)]/10 text-[var(--partial)]"}`}>
            {collection.status}
          </span>
        </div>
      </div>

      {collection.control_ids?.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {collection.control_ids.map(c => (
            <span key={c} className="text-xs px-2 py-1 rounded bg-[var(--accent)]/10 text-[var(--accent)]">{c}</span>
          ))}
        </div>
      )}

      <div className="space-y-2">
        {(collection.evidence_items || []).map(item => (
          <div key={item.id} className="glass overflow-hidden">
            <button onClick={() => setExpanded(expanded === item.id ? null : item.id)}
              className="w-full p-4 flex items-center gap-4 text-left hover:bg-[var(--surface-hover)]/50 transition-colors">
              <div className="flex-1">
                <p className="text-sm font-semibold text-[var(--fg)] capitalize">{item.evidence_type.replace(/_/g, " ")}</p>
                <p className="text-xs text-[var(--muted)]">{item.source_system} · Fresh until {new Date(item.freshness_date).toLocaleDateString()}</p>
              </div>
              <div className="flex gap-1">{item.control_mapping?.slice(0, 4).map(c => <span key={c} className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--accent)]/10 text-[var(--accent)]">{c}</span>)}</div>
              <motion.div animate={{ rotate: expanded === item.id ? 180 : 0 }}><ChevronDown size={16} className="text-[var(--muted)]" /></motion.div>
            </button>
            {expanded === item.id && (
              <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} className="overflow-hidden border-t border-[var(--border)]">
                <pre className="p-4 text-xs text-[var(--muted)] overflow-x-auto whitespace-pre-wrap font-mono">{JSON.stringify(item.data, null, 2)}</pre>
              </motion.div>
            )}
          </div>
        ))}
      </div>
    </motion.div>
  );
}
