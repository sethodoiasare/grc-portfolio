"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, Clock, Shield, TrendingUp, Bug, Server, ChevronRight } from "lucide-react";
import Link from "next/link";
import { RiskBadge } from "./_components/RiskBadge";

interface KPI {
  total_open: number; total_closed: number; total_risk_accepted: number;
  breached_count: number; breach_rate_pct: number; mttr_days: number | null;
  critical_open: number; high_open: number; medium_open: number; low_open: number;
  avg_cvss: number;
}

interface OverdueVuln {
  id: number; title: string; severity: string; cvss_score: number;
  asset_hostname: string; days_open: number; sla_breach_days: number; sla_deadline_days: number;
}

interface SevDist { severity: string; count: number; }

interface TimelinePoint { date: string; total_open: number; breached: number; }

export default function DashboardPage() {
  const [kpi, setKpi] = useState<KPI | null>(null);
  const [topOverdue, setTopOverdue] = useState<OverdueVuln[]>([]);
  const [sevDist, setSevDist] = useState<SevDist[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [kpiRes, overdueRes, sevRes, tlRes] = await Promise.all([
        fetch("/api/v1/dashboard/kpis"),
        fetch("/api/v1/dashboard/top-overdue?limit=5"),
        fetch("/api/v1/dashboard/severity-distribution"),
        fetch("/api/v1/dashboard/breach-timeline?days=30"),
      ]);
      if (kpiRes.ok) setKpi(await kpiRes.json());
      if (overdueRes.ok) setTopOverdue(await overdueRes.json());
      if (sevRes.ok) setSevDist(await sevRes.json());
      if (tlRes.ok) setTimeline(await tlRes.json());
      setLoading(false);
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-32 w-full" />)}
      </div>
    );
  }

  const sevColors: Record<string, string> = { Critical: "#f04444", High: "#f5a623", Medium: "#e2c541", Low: "#5b8def", Info: "#6e7687" };
  const maxSev = Math.max(...sevDist.map(d => d.count), 1);

  const formatDate = (d: string) => {
    const date = new Date(d);
    return `${date.getDate()}/${date.getMonth() + 1}`;
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 className="text-xl font-bold text-[var(--fg)] mb-1">SLA Dashboard</h1>
        <p className="text-sm text-[var(--muted)] mb-6">Patch & vulnerability SLA compliance overview</p>
      </motion.div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard icon={Bug} label="Open Vulns" value={kpi?.total_open ?? 0} sub={`${kpi?.breached_count ?? 0} breached`} accent="var(--fail)" delay={0} />
        <KpiCard icon={AlertTriangle} label="Breach Rate" value={`${kpi?.breach_rate_pct ?? 0}%`} sub={`Critical: ${kpi?.critical_open ?? 0}`} accent="var(--partial)" delay={1} />
        <KpiCard icon={Clock} label="MTTR" value={kpi?.mttr_days ? `${kpi.mttr_days}d` : "—"} sub={`Avg CVSS: ${kpi?.avg_cvss ?? 0}`} accent="var(--accent)" delay={2} />
        <KpiCard icon={Activity} label="Closed / Accepted" value={kpi ? (kpi.total_closed + kpi.total_risk_accepted) : 0} sub={`${kpi?.total_closed ?? 0} closed, ${kpi?.total_risk_accepted ?? 0} accepted`} accent="var(--pass)" delay={3} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Severity Distribution */}
        <motion.div className="glass p-5" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <h2 className="text-sm font-semibold text-[var(--fg)] mb-4">Severity Distribution (Open)</h2>
          <div className="space-y-3">
            {sevDist.map((d) => (
              <div key={d.severity} className="flex items-center gap-3">
                <span className="w-16 text-xs text-[var(--muted)]">{d.severity}</span>
                <div className="flex-1 h-5 bg-[var(--surface-hover)] rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: sevColors[d.severity] || "#6e7687" }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(d.count / maxSev) * 100}%` }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                  />
                </div>
                <span className="w-8 text-right text-xs font-mono text-[var(--fg)]">{d.count}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Breach Timeline Sparkline */}
        <motion.div className="glass p-5" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <h2 className="text-sm font-semibold text-[var(--fg)] mb-4">Breach Trend (30d)</h2>
          <div className="flex items-end gap-[2px] h-40">
            {timeline.map((p, i) => {
              const maxH = 140;
              const hPct = p.total_open > 0 ? (p.breached / p.total_open) * 100 : 0;
              const h = Math.max(4, (hPct / 100) * maxH);
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1" title={`${p.date}: ${p.breached}/${p.total_open} breached`}>
                  <span className="text-[9px] text-[var(--muted)]">{p.breached}</span>
                  <div className="w-full rounded-t-sm" style={{ height: `${h}px`, backgroundColor: hPct > 50 ? "var(--fail)" : "var(--partial)", opacity: hPct > 0 ? 0.8 : 0.3 }} />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-2 text-[10px] text-[var(--muted)]">
            <span>{formatDate(timeline[0]?.date || "")}</span>
            <span>{formatDate(timeline[timeline.length - 1]?.date || "")}</span>
          </div>
        </motion.div>
      </div>

      {/* Top Overdue */}
      <motion.div className="glass p-5" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-[var(--fg)]">Top Overdue Vulnerabilities</h2>
          <Link href="/vulnerabilities?sla_breach=breached" className="flex items-center gap-1 text-xs text-[var(--accent)] hover:underline">
            View all <ChevronRight size={14} />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-left text-xs text-[var(--muted)]">
                <th className="pb-2 pr-4 font-medium">Asset</th>
                <th className="pb-2 pr-4 font-medium">Vulnerability</th>
                <th className="pb-2 pr-4 font-medium">Severity</th>
                <th className="pb-2 pr-4 font-medium">CVSS</th>
                <th className="pb-2 pr-4 font-medium">Days Open</th>
                <th className="pb-2 pr-4 font-medium">SLA Deadline</th>
                <th className="pb-2 font-medium">Breach</th>
              </tr>
            </thead>
            <tbody>
              {topOverdue.map((v) => (
                <tr key={v.id} className="border-b border-[var(--border)]/50 hover:bg-[var(--surface-hover)]/50 transition-colors">
                  <td className="py-2.5 pr-4">
                    <div className="flex items-center gap-1.5">
                      <Server size={14} className="text-[var(--muted)]" />
                      <span className="text-[var(--fg)]">{v.asset_hostname}</span>
                    </div>
                  </td>
                  <td className="py-2.5 pr-4 max-w-[280px] truncate text-[var(--fg)]">{v.title}</td>
                  <td className="py-2.5 pr-4"><RiskBadge severity={v.severity} /></td>
                  <td className="py-2.5 pr-4 font-mono text-xs">{v.cvss_score}</td>
                  <td className="py-2.5 pr-4 font-mono text-xs">{v.days_open}d</td>
                  <td className="py-2.5 pr-4 font-mono text-xs text-[var(--muted)]">{v.sla_deadline_days}d</td>
                  <td className="py-2.5">
                    <span className={`font-mono text-xs font-semibold ${v.sla_breach_days > 0 ? "text-[var(--fail)]" : "text-[var(--pass)]"}`}>
                      {v.sla_breach_days > 0 ? `+${v.sla_breach_days}d` : "OK"}
                    </span>
                  </td>
                </tr>
              ))}
              {topOverdue.length === 0 && (
                <tr><td colSpan={7} className="py-8 text-center text-[var(--muted)]">No overdue vulnerabilities</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}

function KpiCard({ icon: Icon, label, value, sub, accent, delay }: { icon: React.ElementType; label: string; value: string | number; sub: string; accent: string; delay: number }) {
  return (
    <motion.div className="glass glass-hover p-5" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: delay * 0.05 }}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-[var(--muted)]">{label}</span>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${accent}15` }}>
          <Icon size={15} style={{ color: accent }} />
        </div>
      </div>
      <div className="text-2xl font-bold counter" style={{ color: accent }}>{value}</div>
      <div className="text-[11px] text-[var(--muted)] mt-1">{sub}</div>
    </motion.div>
  );
}
