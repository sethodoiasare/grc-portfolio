"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Database, Calendar, CheckCircle, AlertTriangle, Loader2, ChevronRight } from "lucide-react";
import { useAuth } from "../_hooks/useAuth";

interface Collection {
  id: number; connector_name: string; market_name: string | null;
  status: string; started_at: string; completed_at: string | null; evidence_count: number;
}

export default function CollectionsPage() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  useEffect(() => {
    fetch("/api/v1/collections", { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setCollections).catch(() => {}).finally(() => setLoading(false));
  }, [token]);

  const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.04 } } };
  const cardItem = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 400, damping: 30 } } };

  return (
    <motion.div className="max-w-6xl mx-auto px-6 py-10" variants={container} initial="hidden" animate="show">
      <motion.div variants={cardItem} className="mb-8">
        <motion.div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-4"
          style={{ background: "rgba(91, 141, 239, 0.08)", color: "var(--accent)", border: "1px solid rgba(91, 141, 239, 0.15)" }}>
          <Database className="w-3 h-3" /> Collections
        </motion.div>
        <h1 className="text-4xl font-bold tracking-[-0.03em] text-[var(--fg)]">Collection History</h1>
        <p className="text-sm text-[var(--muted)] mt-2">{collections.length} runs across all connectors</p>
      </motion.div>

      <div className="space-y-3">
        {loading ? [1,2,3].map(i => <div key={i} className="glass p-5"><div className="skeleton w-48 h-4 rounded" /></div>) : (
          collections.length === 0 ? (
            <div className="text-center py-20"><Database size={40} className="mx-auto mb-4 text-[var(--muted)]/30" /><p className="text-sm text-[var(--muted)]">No collections yet. Run a connector to get started.</p></div>
          ) : (
            collections.map((c) => (
              <motion.div key={c.id} variants={cardItem} className="glass p-5 flex items-center gap-4 hover:bg-[var(--surface-hover)]/50 transition-colors">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ background: c.status === "complete" ? "rgba(38,201,99,0.1)" : "rgba(245,166,35,0.1)" }}>
                  {c.status === "complete" ? <CheckCircle size={18} color="var(--pass)" /> : <Loader2 size={18} color="var(--partial)" className="animate-spin" />}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-[var(--fg)]">{c.connector_name}</p>
                  <p className="text-xs text-[var(--muted)]">
                    {c.market_name || "All markets"} · {c.evidence_count} items · {new Date(c.started_at).toLocaleString()}
                  </p>
                </div>
                <Link href={`/collections/${c.id}`} className="text-[var(--accent)] hover:underline text-xs flex items-center gap-1">
                  Details <ChevronRight size={12} />
                </Link>
              </motion.div>
            ))
          )
        )}
      </div>
    </motion.div>
  );
}
