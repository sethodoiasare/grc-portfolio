"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Radio, Zap, CheckCircle, Clock, AlertTriangle, Play, Loader2, MapPin, Settings } from "lucide-react";
import { useAuth } from "../_hooks/useAuth";
import { ConnectorConfig } from "../_components/ConnectorConfig";

interface Connector {
  id: number; name: string; connector_type: string; mode: string; status: string; last_run: string | null; enabled: number; auth_config: string;
}
interface Market {
  id: number; name: string;
}

export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [markets, setMarkets] = useState<Market[]>([]);
  const [running, setRunning] = useState<number | null>(null);
  const [selectedMarket, setSelectedMarket] = useState<number | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [configConnector, setConfigConnector] = useState<Connector | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    Promise.all([
      fetch("/api/v1/connectors", { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
      fetch("/api/v1/markets", { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
    ]).then(([c, m]) => { setConnectors(c); setMarkets(m); }).catch(() => {}).finally(() => setLoading(false));
  }, [token]);

  async function toggleMode(c: Connector) {
    const newMode = c.mode === "live" ? "simulated" : "live";
    await fetch(`/api/v1/connectors/${c.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ mode: newMode }),
    });
    const res = await fetch("/api/v1/connectors", { headers: { Authorization: `Bearer ${token}` } });
    setConnectors(await res.json());
  }

  async function triggerRun(id: number) {
    setRunning(id);
    setResult(null);
    try {
      const res = await fetch(`/api/v1/connectors/${id}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ market_id: selectedMarket, config: {} }),
      });
      const data = await res.json();
      setResult(`Collected ${data.items_collected} items from ${data.connector} (${data.market})`);
      // Refresh list
      const connRes = await fetch("/api/v1/connectors", { headers: { Authorization: `Bearer ${token}` } });
      setConnectors(await connRes.json());
    } catch {
      setResult("Failed to run connector");
    }
    setRunning(null);
  }

  const statusIcon: Record<string, typeof CheckCircle> = { success: CheckCircle, idle: Clock, running: Zap, error: AlertTriangle };
  const statusColor: Record<string, string> = { success: "var(--pass)", idle: "var(--muted)", running: "var(--accent)", error: "var(--fail)" };

  const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.04 } } };
  const cardItem = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 400, damping: 30 } } };

  return (
    <motion.div className="max-w-6xl mx-auto px-6 py-10" variants={container} initial="hidden" animate="show">
      <motion.div variants={cardItem} className="mb-8">
        <motion.div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-4"
          style={{ background: "rgba(91, 141, 239, 0.08)", color: "var(--accent)", border: "1px solid rgba(91, 141, 239, 0.15)" }}>
          <Radio className="w-3 h-3" /> Connectors
        </motion.div>
        <h1 className="text-4xl font-bold tracking-[-0.03em] text-[var(--fg)]">Evidence Connectors</h1>
        <p className="text-sm text-[var(--muted)] mt-2">Run connectors to pull simulated audit evidence from 7 systems.</p>
      </motion.div>

      {/* Market selector */}
      <motion.div variants={cardItem} className="flex items-center gap-3 mb-6">
        <span className="text-xs text-[var(--muted)]">Market:</span>
        <select
          value={selectedMarket || ""}
          onChange={(e) => setSelectedMarket(e.target.value ? Number(e.target.value) : null)}
          className="px-3 py-2 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)]"
        >
          <option value="">Any market</option>
          {markets.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
      </motion.div>

      {result && (
        <motion.div variants={cardItem} className="mb-4 px-4 py-3 rounded-lg text-sm"
          style={{ background: "rgba(38,201,99,0.08)", border: "1px solid rgba(38,201,99,0.2)", color: "var(--pass)" }}>
          {result}
        </motion.div>
      )}

      <div className="space-y-3">
        {loading ? [1,2,3].map(i => <div key={i} className="glass p-5"><div className="skeleton w-48 h-4 rounded" /></div>) : (
          connectors.map((c) => {
            const Icon = statusIcon[c.status] || Clock;
            return (
              <motion.div key={c.id} variants={cardItem} className="glass p-5 flex items-center gap-4 hover:bg-[var(--surface-hover)]/50 transition-colors">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: `${statusColor[c.status]}12` }}>
                  <Icon size={18} style={{ color: statusColor[c.status] }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-[var(--fg)]">{c.name}</p>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                      c.mode === "live" ? "bg-[var(--pass)]/10 text-[var(--pass)]" : "bg-[var(--partial)]/10 text-[var(--partial)]"
                    }`}>
                      {c.mode === "live" ? "LIVE" : "SIM"}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--muted)]">
                    {c.connector_type} · {c.mode === "live" ? "Real system" : "Simulated data"} · Last run: {c.last_run ? new Date(c.last_run).toLocaleDateString() : "Never"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setConfigConnector(c); }}
                  className="flex items-center gap-1 text-[10px] px-2 py-1 rounded border border-[var(--border)] text-[var(--muted)] hover:text-[var(--fg)] hover:border-[var(--accent)] transition-colors"
                >
                  <Settings size={11} />
                  Configure
                </button>
                <button
                  type="button"
                  onClick={() => toggleMode(c)}
                  className="text-[10px] px-2 py-1 rounded border border-[var(--border)] text-[var(--muted)] hover:text-[var(--fg)] hover:border-[var(--accent)] transition-colors"
                >
                  {c.mode === "live" ? "Switch to Sim" : "Switch to Live"}
                </button>
                <button
                  type="button"
                  onClick={() => triggerRun(c.id)}
                  disabled={running === c.id || !c.enabled}
                  className="flex items-center gap-1.5 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-semibold disabled:opacity-40 hover:bg-[var(--accent-soft)] transition-colors"
                >
                  {running === c.id ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                  Run
                </button>
              </motion.div>
            );
          })
        )}
      </div>

      {configConnector && (
        <ConnectorConfig
          connectorId={configConnector.id}
          connectorName={configConnector.name}
          connectorType={configConnector.connector_type}
          mode={configConnector.mode}
          authConfig={configConnector.auth_config ? JSON.parse(configConnector.auth_config) : {}}
          open={!!configConnector}
          onClose={() => setConfigConnector(null)}
          onSaved={async () => {
            const res = await fetch("/api/v1/connectors", { headers: { Authorization: `Bearer ${token}` } });
            setConnectors(await res.json());
          }}
        />
      )}
    </motion.div>
  );
}
