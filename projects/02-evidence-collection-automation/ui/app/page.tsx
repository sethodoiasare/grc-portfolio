"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Activity, Radio, Database, Package, Layers, Sparkles,
  CheckCircle, AlertTriangle, Clock, ArrowRight, Zap,
} from "lucide-react";
import { useAuth } from "./_hooks/useAuth";

interface Stats {
  total_items: number;
  fresh_items: number;
  stale_items: number;
  by_connector: { name: string; type: string; count: number }[];
}

interface Connector {
  id: number;
  name: string;
  connector_type: string;
  status: string;
  last_run: string | null;
}

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.05 } },
};
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 400, damping: 30 } },
};

function SkeletonCard() {
  return <div className="glass p-6"><div className="skeleton w-16 h-4 rounded mb-2" /><div className="skeleton w-32 h-8 rounded" /></div>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  useEffect(() => {
    async function load() {
      try {
        const [statsRes, connRes] = await Promise.all([
          fetch("/api/v1/evidence/stats", { headers: { Authorization: `Bearer ${token}` } }),
          fetch("/api/v1/connectors", { headers: { Authorization: `Bearer ${token}` } }),
        ]);
        if (statsRes.ok) setStats(await statsRes.json());
        if (connRes.ok) setConnectors(await connRes.json());
      } catch {}
      setLoading(false);
    }
    load();
  }, [token]);

  const statusConfig: Record<string, { icon: typeof CheckCircle; color: string }> = {
    success: { icon: CheckCircle, color: "var(--pass)" },
    idle: { icon: Clock, color: "var(--muted)" },
    running: { icon: Zap, color: "var(--accent)" },
    error: { icon: AlertTriangle, color: "var(--fail)" },
  };

  return (
    <motion.div className="max-w-6xl mx-auto px-6 py-10" variants={container} initial="hidden" animate="show">
      {/* Header */}
      <motion.div variants={item} className="mb-10">
        <motion.div
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-4"
          style={{ background: "rgba(91, 141, 239, 0.08)", color: "var(--accent)", border: "1px solid rgba(91, 141, 239, 0.15)" }}
          initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, type: "spring", stiffness: 500 }}
        >
          <Sparkles className="w-3 h-3" />
          Evidence Collection
        </motion.div>
        <h1 className="text-4xl font-bold tracking-[-0.03em] text-[var(--fg)] leading-tight">
          Collection<br /><span className="text-[var(--muted)]">Dashboard</span>
        </h1>
        <p className="text-sm text-[var(--muted)] mt-3 max-w-md leading-relaxed">
          Automated evidence collection across 7 systems. Run connectors to pull audit evidence, then bundle for assessment.
        </p>
      </motion.div>

      {/* Stat cards */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          {[1,2,3].map(i => <SkeletonCard key={i} />)}
        </div>
      ) : (
        <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <div className="glass p-6">
            <p className="text-xs text-[var(--muted)] uppercase tracking-wider mb-1">Total Evidence</p>
            <p className="text-3xl font-bold text-[var(--fg)]">{stats?.total_items || 0}</p>
          </div>
          <div className="glass p-6">
            <p className="text-xs text-[var(--muted)] uppercase tracking-wider mb-1">Fresh Items</p>
            <p className="text-3xl font-bold text-[var(--pass)]">{stats?.fresh_items || 0}</p>
          </div>
          <div className="glass p-6">
            <p className="text-xs text-[var(--muted)] uppercase tracking-wider mb-1">Stale Items</p>
            <p className="text-3xl font-bold text-[var(--partial)]">{stats?.stale_items || 0}</p>
          </div>
        </motion.div>
      )}

      {/* Connectors */}
      <motion.div variants={item} className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-[var(--fg)]">Connectors</h2>
          <Link href="/connectors" className="text-xs text-[var(--accent)] hover:underline flex items-center gap-1">
            View all <ArrowRight size={12} />
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {loading ? [1,2,3,4].map(i => <SkeletonCard key={i} />) : (
            connectors.slice(0, 4).map((c) => {
              const config = statusConfig[c.status] || statusConfig.idle;
              const Icon = config.icon;
              return (
                <div key={c.id} className="glass p-4 hover:bg-[var(--surface-hover)]/50 transition-colors">
                  <div className="flex items-center gap-2 mb-2">
                    <Radio size={14} style={{ color: config.color }} />
                    <span className="text-sm font-semibold text-[var(--fg)] truncate">{c.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ background: config.color }} />
                    <span className="text-xs text-[var(--muted)] capitalize">{c.status}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </motion.div>

      {/* Quick links */}
      <motion.div variants={item} className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { href: "/connectors", label: "Run Connectors", icon: Radio },
          { href: "/collections", label: "Collections", icon: Database },
          { href: "/evidence", label: "Evidence Library", icon: Layers },
          { href: "/bundles", label: "Bundles", icon: Package },
        ].map(({ href, label, icon: Icon }) => (
          <Link key={href} href={href} className="glass p-4 hover:bg-[var(--surface-hover)]/50 transition-all text-center">
            <Icon size={20} className="mx-auto mb-2 text-[var(--accent)]" />
            <span className="text-xs font-medium text-[var(--fg)]">{label}</span>
          </Link>
        ))}
      </motion.div>
    </motion.div>
  );
}
