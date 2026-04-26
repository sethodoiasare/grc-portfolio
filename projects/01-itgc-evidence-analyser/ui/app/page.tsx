"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAuth } from "./_hooks/useAuth";
import {
  Shield,
  Activity,
  BarChart3,
  Layers,
  ArrowRight,
  ClipboardCheck,
  Sparkles,
  ChevronRight,
} from "lucide-react";

const API = "/api/v1";

interface AssessmentResult {
  control_id: string;
  control_name: string;
  verdict: string;
  confidence: number;
  risk_rating: string;
  gaps: string[];
  draft_finding: {
    title: string;
    observation: string;
    criteria: string;
    risk_impact: string;
    recommendation: string;
    management_action: string;
  } | null;
  assessed_at: string;
  tokens_used: number;
  satisfied_requirements: string[];
  recommended_evidence: string[];
  remediation_notes: string;
}

interface Control {
  control_id: string;
  control_name: string;
  domain: string;
  d_statements: string[];
  e_statements: string[];
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.05 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { type: "spring" as const, stiffness: 400, damping: 30 },
  },
};

function AnimatedNumber({ value }: { value: number | string }) {
  if (typeof value === "string") return <>{value}</>;
  const prevRef = useRef(0);
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const start = prevRef.current;
    const end = value;
    const duration = 600;
    const startTime = performance.now();

    function tick(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(start + (end - start) * eased));
      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
    prevRef.current = end;
  }, [value]);

  return <>{display.toLocaleString()}</>;
}

function SkeletonCard() {
  return (
    <div className="glass p-5 space-y-4">
      <div className="flex items-center gap-3">
        <div className="skeleton w-9 h-9 rounded-lg" />
        <div className="skeleton w-16 h-3 rounded" />
      </div>
      <div className="skeleton w-20 h-8 rounded" />
    </div>
  );
}

const statusConfig: Record<string, { color: string; bg: string; ring: string }> = {
  PASS: { color: "var(--pass)", bg: "bg-[var(--pass)]/10", ring: "ring-[var(--pass)]/20" },
  PARTIAL: { color: "var(--partial)", bg: "bg-[var(--partial)]/10", ring: "ring-[var(--partial)]/20" },
  FAIL: { color: "var(--fail)", bg: "bg-[var(--fail)]/10", ring: "ring-[var(--fail)]/20" },
  INSUFFICIENT_EVIDENCE: { color: "var(--insufficient)", bg: "bg-[var(--insufficient)]/10", ring: "ring-[var(--insufficient)]/20" },
};

export default function DashboardPage() {
  const [controls, setControls] = useState<Control[]>([]);
  const [results, setResults] = useState<AssessmentResult[]>([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  useEffect(() => {
    async function load() {
      try {
        const [ctrlRes, assessRes] = await Promise.all([
          fetch(`${API}/controls`),
          fetch(`${API}/assessments`, { headers: { Authorization: `Bearer ${token}` } }),
        ]);
        const ctrls: Control[] = await ctrlRes.json();
        setControls(ctrls);
        if (assessRes.ok) {
          const data = await assessRes.json();
          setResults(Array.isArray(data) ? data : []);
        }
      } catch {
        // API may not be running yet
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [token]);

  const domains = [...new Set(controls.map((c) => c.domain))].sort();
  const verdictCounts = { PASS: 0, PARTIAL: 0, FAIL: 0, INSUFFICIENT_EVIDENCE: 0 };
  results.forEach((r) => {
    verdictCounts[r.verdict as keyof typeof verdictCounts]++;
  });

  const passRate = results.length
    ? Math.round((verdictCounts.PASS / results.length) * 100)
    : 0;

  return (
    <motion.div
      className="max-w-6xl mx-auto px-6 py-10"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Hero header — asymmetric layout */}
      <motion.div variants={item} className="mb-12">
        <div className="flex items-start justify-between">
          <div>
            <motion.div
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-4"
              style={{
                background: "rgba(91, 141, 239, 0.08)",
                color: "var(--accent)",
                border: "1px solid rgba(91, 141, 239, 0.15)",
              }}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1, type: "spring", stiffness: 500 }}
            >
              <Sparkles className="w-3 h-3" />
              AI-Powered GRC
            </motion.div>
            <h1 className="text-4xl font-bold tracking-[-0.03em] text-[var(--fg)] leading-tight">
              Control Assurance
              <br />
              <span className="text-[var(--muted)]">Dashboard</span>
            </h1>
            <p className="text-sm text-[var(--muted)] mt-3 max-w-md leading-relaxed">
              Real-time evidence assessment across {controls.length || "—"} Vodafone ITGC controls
              with AI-driven verdict analysis.
            </p>
          </div>
          {/* Decorative stat */}
          <motion.div
            className="hidden lg:block glass p-6 text-center"
            variants={item}
            whileHover={{ scale: 1.02 }}
          >
            <div className="text-xs text-[var(--muted)] font-medium mb-1">Pass Rate</div>
            <div className="text-4xl font-bold text-[var(--pass)] counter">
              {loading ? "—" : `${passRate}%`}
            </div>
            <div className="text-xs text-[var(--muted)] mt-1">
              {results.length} assessments
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Stat cards — varied sizing, not equal columns */}
      <motion.div
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10"
        variants={container}
        initial="hidden"
        animate="show"
      >
        {loading ? (
          <>
            <div><SkeletonCard /></div>
            <div><SkeletonCard /></div>
            <div><SkeletonCard /></div>
          </>
        ) : (
          <>
            {/* Controls */}
            <motion.div
              variants={item}
              whileHover={{ y: -3 }}
              className="glass p-5 spotlight group cursor-default"
            >
              <div className="flex items-center gap-3 mb-3">
                <motion.div
                  whileHover={{ rotate: [0, -5, 5, 0] }}
                  transition={{ duration: 0.4 }}
                  className="w-10 h-10 rounded-xl bg-[var(--accent)]/10 flex items-center justify-center ring-1 ring-[var(--accent)]/15"
                >
                  <Layers className="w-5 h-5 text-[var(--accent)]" />
                </motion.div>
                <span className="text-xs text-[var(--muted)] font-medium tracking-wide uppercase">
                  Controls
                </span>
              </div>
              <p className="text-4xl font-bold text-[var(--fg)] counter tracking-[-0.02em]">
                <AnimatedNumber value={controls.length} />
              </p>
              <p className="text-xs text-[var(--muted)] mt-1.5">
                across {domains.length} domains
              </p>
            </motion.div>

            {/* Domains */}
            <motion.div
              variants={item}
              whileHover={{ y: -3 }}
              className="glass p-5 spotlight group cursor-default"
            >
              <div className="flex items-center gap-3 mb-3">
                <motion.div
                  whileHover={{ rotate: [0, -5, 5, 0] }}
                  transition={{ duration: 0.4 }}
                  className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center ring-1 ring-purple-500/15"
                >
                  <BarChart3 className="w-5 h-5 text-purple-400" />
                </motion.div>
                <span className="text-xs text-[var(--muted)] font-medium tracking-wide uppercase">
                  Domains
                </span>
              </div>
              <p className="text-4xl font-bold text-[var(--fg)] counter tracking-[-0.02em]">
                <AnimatedNumber value={domains.length} />
              </p>
              <p className="text-xs text-[var(--muted)] mt-1.5">
                control families
              </p>
            </motion.div>

            {/* Assessments */}
            <motion.div
              variants={item}
              whileHover={{ y: -3 }}
              className="glass p-5 spotlight group cursor-default"
            >
              <div className="flex items-center gap-3 mb-3">
                <motion.div
                  whileHover={{ rotate: [0, -5, 5, 0] }}
                  transition={{ duration: 0.4 }}
                  className="w-10 h-10 rounded-xl bg-[var(--pass)]/10 flex items-center justify-center ring-1 ring-[var(--pass)]/15"
                >
                  <Activity className="w-5 h-5 text-[var(--pass)]" />
                </motion.div>
                <span className="text-xs text-[var(--muted)] font-medium tracking-wide uppercase">
                  Assessments
                </span>
              </div>
              <p className="text-4xl font-bold text-[var(--fg)] counter tracking-[-0.02em]">
                <AnimatedNumber value={results.length || 0} />
              </p>
              <p className="text-xs text-[var(--muted)] mt-1.5">
                {results.length > 0 ? `${passRate}% compliant` : "no assessments yet"}
              </p>
            </motion.div>

          </>
        )}
      </motion.div>

      {/* Main content — asymmetric 5+4 grid */}
      <div className="grid grid-cols-1 lg:grid-cols-9 gap-6 mb-10">
        {/* Domain breakdown — spans 5 */}
        <motion.div
          variants={item}
          className="lg:col-span-5 glass p-6"
        >
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-semibold text-[var(--fg)] tracking-tight">
              Controls by Domain
            </h2>
            <span className="text-xs text-[var(--muted)]">{controls.length} total</span>
          </div>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="skeleton h-6 rounded" />
              ))}
            </div>
          ) : (
            <div className="space-y-2.5">
              {domains.map((d, idx) => {
                const count = controls.filter((c) => c.domain === d).length;
                const pct = (count / controls.length) * 100;
                return (
                  <motion.div
                    key={d}
                    className="flex items-center gap-3 group"
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + idx * 0.04, type: "spring", stiffness: 300 }}
                  >
                    <span className="text-xs font-medium text-[var(--muted)] w-24 shrink-0">
                      {d}
                    </span>
                    <div className="flex-1 h-2 bg-[var(--surface-hover)] rounded-full overflow-hidden">
                      <motion.div
                        className="h-full rounded-full"
                        style={{
                          background: `linear-gradient(90deg, var(--accent), rgba(91, 141, 239, 0.6))`,
                        }}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.8, delay: 0.2 + idx * 0.04, ease: [0.34, 1.56, 0.64, 1] }}
                      />
                    </div>
                    <span className="text-xs font-mono text-[var(--muted)] w-8 text-right tabular-nums">
                      {count}
                    </span>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>

        {/* Verdict distribution — spans 4 */}
        <motion.div
          variants={item}
          className="lg:col-span-4 glass p-6"
        >
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-semibold text-[var(--fg)] tracking-tight">
              Verdict Distribution
            </h2>
            <span className="text-xs text-[var(--muted)]">{results.length} verdicts</span>
          </div>
          {results.length === 0 ? (
            <motion.div
              className="flex flex-col items-center justify-center py-8 text-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <div className="w-14 h-14 rounded-2xl bg-[var(--accent)]/5 flex items-center justify-center mb-4">
                <Shield className="w-7 h-7 text-[var(--muted)]" />
              </div>
              <p className="text-sm text-[var(--muted)] font-medium">No assessments run yet</p>
              <p className="text-xs text-[var(--muted)]/60 mt-1 max-w-xs">
                Run your first control assessment to see verdict analytics.
              </p>
              <Link
                href="/assess"
                className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-lg text-xs font-medium text-[var(--fg)] bg-[var(--accent)]/10 hover:bg-[var(--accent)]/20 ring-1 ring-[var(--accent)]/20 transition-all duration-200"
              >
                Start Assessment
                <ArrowRight className="w-3 h-3" />
              </Link>
            </motion.div>
          ) : (
            <div className="space-y-2.5">
              {(["PASS", "PARTIAL", "FAIL", "INSUFFICIENT_EVIDENCE"] as const).map((v, idx) => {
                const count = verdictCounts[v];
                const cfg = statusConfig[v];
                const pct = results.length ? (count / results.length) * 100 : 0;
                const labels: Record<string, string> = {
                  PASS: "Pass",
                  PARTIAL: "Partial",
                  FAIL: "Fail",
                  INSUFFICIENT_EVIDENCE: "Insufficient",
                };
                return (
                  <motion.div
                    key={v}
                    className="flex items-center gap-3 group"
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + idx * 0.05, type: "spring", stiffness: 300 }}
                  >
                    <div
                      className="w-2.5 h-2.5 rounded-sm"
                      style={{ backgroundColor: cfg.color }}
                    />
                    <span className="text-xs text-[var(--muted)] flex-1">{labels[v]}</span>
                    <div className="w-24 h-1.5 bg-[var(--surface-hover)] rounded-full overflow-hidden mr-2">
                      <motion.div
                        className="h-full rounded-full"
                        style={{ backgroundColor: cfg.color }}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.6, delay: 0.2 + idx * 0.05, ease: "easeOut" }}
                      />
                    </div>
                    <span className="text-xs font-mono tabular-nums text-[var(--fg)] w-5 text-right">
                      {count}
                    </span>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>
      </div>

      {/* Quick actions — two cards, asymmetric styling */}
      <motion.div
        className="grid grid-cols-1 sm:grid-cols-5 gap-4"
        variants={item}
      >
        <Link
          href="/controls"
          className="sm:col-span-3 glass glass-hover p-5 flex items-center gap-4 group relative overflow-hidden spotlight"
        >
          <motion.div
            whileHover={{ scale: 1.08, rotate: -3 }}
            transition={{ type: "spring", stiffness: 400 }}
            className="w-11 h-11 rounded-xl bg-[var(--accent)]/10 flex items-center justify-center ring-1 ring-[var(--accent)]/15 shrink-0"
          >
            <Shield className="w-5 h-5 text-[var(--accent)]" />
          </motion.div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-[var(--fg)]">Browse Controls Library</p>
            <p className="text-xs text-[var(--muted)] mt-0.5 truncate">
              {controls.length} Vodafone ITGC controls with D/E statements
            </p>
          </div>
          <motion.div
            className="shrink-0"
            whileHover={{ x: 3 }}
            transition={{ type: "spring", stiffness: 500 }}
          >
            <ArrowRight className="w-4 h-4 text-[var(--muted)]" />
          </motion.div>
        </Link>

        <Link
          href="/assessments"
          className="sm:col-span-2 glass glass-hover p-5 flex items-center gap-4 group relative overflow-hidden spotlight"
        >
          <motion.div
            whileHover={{ scale: 1.08, rotate: 3 }}
            transition={{ type: "spring", stiffness: 400 }}
            className="w-11 h-11 rounded-xl bg-[var(--pass)]/10 flex items-center justify-center ring-1 ring-[var(--pass)]/15 shrink-0"
          >
            <ClipboardCheck className="w-5 h-5 text-[var(--pass)]" />
          </motion.div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-[var(--fg)]">View Assessments</p>
            <p className="text-xs text-[var(--muted)] mt-0.5 truncate">
              {results.length} completed — review findings, evidence, and audit opinions
            </p>
          </div>
          <motion.div
            className="shrink-0"
            whileHover={{ x: 3 }}
            transition={{ type: "spring", stiffness: 500 }}
          >
            <ChevronRight className="w-4 h-4 text-[var(--muted)]" />
          </motion.div>
        </Link>
      </motion.div>

      {/* Footer */}
      <motion.div
        variants={item}
        className="mt-12 pt-6 border-t border-[var(--border)] flex items-center justify-between text-xs text-[var(--muted)]/60"
      >
        <span>Vodafone ITGC v1.0</span>
        <span>AI Control Assurance Engine</span>
      </motion.div>
    </motion.div>
  );
}
