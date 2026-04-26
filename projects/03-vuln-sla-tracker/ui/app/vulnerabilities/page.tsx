"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Filter, Server, ChevronDown, Download, Shield } from "lucide-react";
import { RiskBadge } from "../_components/RiskBadge";

interface Vuln {
  id: number; title: string; severity: string; cvss_score: number;
  cve_id: string; asset_hostname: string; asset_ip: string;
  scanner_type: string; status: string; days_open: number;
  sla_deadline_days: number; sla_breach_days: number;
  port: number | null; protocol: string; solution: string;
  first_seen: string; last_seen: string;
}

interface VulnResponse { total: number; items: Vuln[]; }

export default function VulnerabilitiesPage() {
  const [data, setData] = useState<VulnResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");
  const [slaBreach, setSlaBreach] = useState("");
  const [sortBy, setSortBy] = useState("first_seen_desc");
  const [page, setPage] = useState(0);
  const limit = 50;

  useEffect(() => {
    async function load() {
      setLoading(true);
      const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit), sort_by: sortBy });
      if (search) params.set("search", search);
      if (status) params.set("status", status);
      if (severity) params.set("severity", severity);
      if (slaBreach) params.set("sla_breach", slaBreach);
      const res = await fetch(`/api/v1/vulnerabilities?${params}`);
      if (res.ok) setData(await res.json());
      setLoading(false);
    }
    load();
  }, [search, status, severity, slaBreach, sortBy, page]);

  const totalPages = data ? Math.ceil(data.total / limit) : 1;

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-xl font-bold text-[var(--fg)] mb-1">Vulnerabilities</h1>
        <p className="text-sm text-[var(--muted)] mb-6">{data?.total ?? 0} findings across all scanners</p>
      </motion.div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="flex items-center gap-2 flex-1 min-w-[200px]">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
            <input
              type="text" placeholder="Search hostname, title, CVE..."
              value={search} onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              className="w-full pl-8 pr-3 py-2 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] outline-none focus:border-[var(--accent)] placeholder:text-[var(--muted)]"
            />
          </div>
        </div>

        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(0); }} className="pl-3 pr-8 py-2 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] outline-none">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
          <option value="risk_accepted">Risk Accepted</option>
          <option value="false_positive">False Positive</option>
        </select>

        <select value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(0); }} className="pl-3 pr-8 py-2 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] outline-none">
          <option value="">All Severities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>

        <select value={slaBreach} onChange={(e) => { setSlaBreach(e.target.value); setPage(0); }} className="pl-3 pr-8 py-2 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] outline-none">
          <option value="">SLA: All</option>
          <option value="breached">Breached</option>
          <option value="compliant">Compliant</option>
        </select>

        <select value={sortBy} onChange={(e) => { setSortBy(e.target.value); setPage(0); }} className="pl-3 pr-8 py-2 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] outline-none">
          <option value="first_seen_desc">Newest First</option>
          <option value="first_seen_asc">Oldest First</option>
          <option value="cvss_desc">CVSS (Highest)</option>
          <option value="cvss_asc">CVSS (Lowest)</option>
          <option value="hostname">Hostname</option>
        </select>

        <a href="/api/v1/export/vulnerabilities" className="flex items-center gap-1.5 px-3 py-2 bg-[var(--accent)]/10 border border-[var(--accent)]/25 rounded-lg text-xs text-[var(--accent)] hover:bg-[var(--accent)]/15 transition-colors">
          <Download size={14} /> Export CSV
        </a>
      </div>

      {/* Table */}
      <div className="glass overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-left text-xs text-[var(--muted)]">
                <th className="py-3 px-4 font-medium">Asset</th>
                <th className="py-3 px-4 font-medium">Vulnerability</th>
                <th className="py-3 px-4 font-medium">Severity</th>
                <th className="py-3 px-4 font-medium">CVSS</th>
                <th className="py-3 px-4 font-medium">CVE</th>
                <th className="py-3 px-4 font-medium">Status</th>
                <th className="py-3 px-4 font-medium">Days Open</th>
                <th className="py-3 px-4 font-medium">SLA Breach</th>
              </tr>
            </thead>
            <tbody>
              {loading && [...Array(10)].map((_, i) => (
                <tr key={i} className="border-b border-[var(--border)]/30"><td colSpan={8} className="py-4 px-4"><div className="skeleton h-6 w-full" /></td></tr>
              ))}
              {!loading && data?.items.map((v) => (
                <tr key={v.id} className="border-b border-[var(--border)]/30 hover:bg-[var(--surface-hover)]/50 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5">
                      <Server size={14} className="text-[var(--muted)]" />
                      <div>
                        <div className="text-[var(--fg)] text-sm">{v.asset_hostname}</div>
                        <div className="text-[10px] text-[var(--muted)]">{v.asset_ip}{v.port ? `:${v.port}` : ""}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 max-w-[240px]">
                    <div className="truncate text-[var(--fg)]" title={v.title}>{v.title}</div>
                    <div className="text-[10px] text-[var(--muted)]">{v.scanner_type}</div>
                  </td>
                  <td className="py-3 px-4"><RiskBadge severity={v.severity} /></td>
                  <td className="py-3 px-4 font-mono text-xs">{v.cvss_score}</td>
                  <td className="py-3 px-4 font-mono text-xs text-[var(--accent)]">{v.cve_id || "—"}</td>
                  <td className="py-3 px-4">
                    <span className={`text-xs font-medium ${v.status === "open" ? "text-[var(--partial)]" : v.status === "closed" ? "text-[var(--pass)]" : "text-[var(--muted)]"}`}>
                      {v.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs">{v.days_open}d</td>
                  <td className="py-3 px-4">
                    <span className={`font-mono text-xs font-semibold ${v.sla_breach_days > 0 ? "text-[var(--fail)]" : "text-[var(--pass)]"}`}>
                      {v.sla_breach_days > 0 ? `+${v.sla_breach_days}d` : "OK"}
                    </span>
                  </td>
                </tr>
              ))}
              {!loading && data?.items.length === 0 && (
                <tr><td colSpan={8} className="py-12 text-center text-[var(--muted)]">No vulnerabilities found</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--border)]">
            <span className="text-xs text-[var(--muted)]">Page {page + 1} of {totalPages} ({data?.total} total)</span>
            <div className="flex gap-2">
              <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="px-3 py-1 text-xs bg-[var(--surface-hover)] border border-[var(--border)] rounded text-[var(--fg)] hover:bg-[var(--surface-elevated)] disabled:opacity-40 transition-colors">Prev</button>
              <button onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page >= totalPages - 1} className="px-3 py-1 text-xs bg-[var(--surface-hover)] border border-[var(--border)] rounded text-[var(--fg)] hover:bg-[var(--surface-elevated)] disabled:opacity-40 transition-colors">Next</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
