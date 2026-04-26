"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ChevronRight, Shield, X, Sparkles, Layers } from "lucide-react";

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

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.04, delayChildren: 0.05 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 400, damping: 30 } },
};

function SkeletonRow() {
  return (
    <div className="glass p-4 flex items-center gap-4">
      <div className="skeleton w-10 h-10 rounded-lg" />
      <div className="flex-1 space-y-2">
        <div className="skeleton w-24 h-3 rounded" />
        <div className="skeleton w-48 h-3 rounded" />
        <div className="skeleton w-64 h-2.5 rounded" />
      </div>
    </div>
  );
}

export default function ControlsPage() {
  const [controls, setControls] = useState<Control[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [domainFilter, setDomainFilter] = useState<string | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch(`${API}/controls`)
      .then((r) => r.json())
      .then(setControls)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const domains = useMemo(() => [...new Set(controls.map((c) => c.domain))].sort(), [controls]);

  const filtered = useMemo(() => {
    let list = controls;
    if (domainFilter) list = list.filter((c) => c.domain === domainFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (c) =>
          c.control_id.toLowerCase().includes(q) ||
          c.control_name.toLowerCase().includes(q) ||
          c.domain.toLowerCase().includes(q) ||
          c.d_statements.some((s) => s.text.toLowerCase().includes(q)) ||
          c.e_statements.some((s) => s.text.toLowerCase().includes(q))
      );
    }
    return list;
  }, [controls, search, domainFilter]);

  return (
    <motion.div
      className="max-w-6xl mx-auto px-6 py-10"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Header */}
      <motion.div variants={item} className="mb-8">
        <motion.div
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-4"
          style={{ background: "rgba(91, 141, 239, 0.08)", color: "var(--accent)", border: "1px solid rgba(91, 141, 239, 0.15)" }}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, type: "spring", stiffness: 500 }}
        >
          <Layers className="w-3 h-3" />
          Controls Library
        </motion.div>
        <h1 className="text-4xl font-bold tracking-[-0.03em] text-[var(--fg)] leading-tight">
          Vodafone ITGC
          <br />
          <span className="text-[var(--muted)]">Controls</span>
        </h1>
        <p className="text-sm text-[var(--muted)] mt-3 max-w-md leading-relaxed">
          {controls.length} controls across {domains.length} domains with design and evidence requirements.
        </p>
      </motion.div>

      {/* Search & Filter */}
      <motion.div variants={item} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-8">
        <div className="flex-1 relative">
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: search.length > 0 ? 1 : 0 }}
            className="absolute inset-0 bg-[var(--accent)]/5 rounded-lg origin-left"
          />
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
          <input
            ref={searchRef}
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search controls, statements, domains..."
            className="w-full h-11 pl-10 pr-10 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] placeholder:text-[var(--muted)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25 focus:border-[var(--accent)]/40 transition-all"
          />
          {search && (
            <motion.button
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              onClick={() => setSearch("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)] hover:text-[var(--fg)] transition-colors"
            >
              <X className="w-4 h-4" />
            </motion.button>
          )}
        </div>

        <div className="flex gap-1.5 flex-wrap">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => setDomainFilter(null)}
            className={`px-3.5 py-2 text-xs rounded-lg transition-all duration-200 ${
              !domainFilter
                ? "bg-[var(--accent)]/10 text-[var(--accent)] font-medium ring-1 ring-[var(--accent)]/20"
                : "bg-[var(--surface)] text-[var(--muted)] ring-1 ring-[var(--border)] hover:text-[var(--fg)] hover:ring-[var(--border-hover)]"
            }`}
          >
            All
          </motion.button>
          {domains.map((d) => (
            <motion.button
              key={d}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setDomainFilter(domainFilter === d ? null : d)}
              className={`px-3.5 py-2 text-xs rounded-lg transition-all duration-200 ${
                domainFilter === d
                  ? "bg-[var(--accent)]/10 text-[var(--accent)] font-medium ring-1 ring-[var(--accent)]/20"
                  : "bg-[var(--surface)] text-[var(--muted)] ring-1 ring-[var(--border)] hover:text-[var(--fg)] hover:ring-[var(--border-hover)]"
              }`}
            >
              {d}
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Results count */}
      {!loading && (
        <motion.p variants={item} className="text-xs text-[var(--muted)] mb-4">
          {filtered.length} control{filtered.length !== 1 ? "s" : ""}
          {search && ` matching "${search}"`}
          {domainFilter && ` in ${domainFilter}`}
        </motion.p>
      )}

      {/* Controls List */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => <SkeletonRow key={i} />)}
        </div>
      ) : filtered.length === 0 ? (
        <motion.div variants={item} className="glass p-16 text-center">
          <motion.div
            animate={{ rotate: [0, -5, 5, 0] }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Shield className="w-10 h-10 mx-auto mb-4 text-[var(--muted)]/30" />
          </motion.div>
          <p className="text-sm text-[var(--muted)]">No controls match your search</p>
          <button
            onClick={() => { setSearch(""); setDomainFilter(null); }}
            className="text-xs text-[var(--accent)] hover:underline mt-2"
          >
            Clear filters
          </button>
        </motion.div>
      ) : (
        <motion.div className="space-y-2" variants={container} initial="hidden" animate="show">
          <AnimatePresence mode="popLayout">
            {filtered.map((c) => (
              <motion.div
                key={c.control_id}
                variants={item}
                layout
                exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.15 } }}
              >
                <Link
                  href={`/controls/${c.control_id}`}
                  className="glass glass-hover spotlight group block p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <motion.div
                        whileHover={{ rotate: [0, -3, 3, 0] }}
                        transition={{ duration: 0.3 }}
                        className="w-10 h-10 rounded-lg bg-[var(--surface-elevated)] flex items-center justify-center font-mono text-xs font-bold text-[var(--accent)] ring-1 ring-[var(--border)]"
                      >
                        {c.control_id.split("_")[0].slice(0, 3)}
                      </motion.div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] text-[var(--muted)]">{c.control_id}</span>
                          <span className="px-1.5 py-0.5 text-[10px] rounded-md bg-[var(--accent)]/10 text-[var(--accent)] font-medium">
                            {c.domain}
                          </span>
                          <span className="text-[10px] text-[var(--muted)]">
                            {c.d_statements.length}D / {c.e_statements.length}E
                          </span>
                        </div>
                        <p className="text-sm text-[var(--fg)] mt-0.5 font-medium">{c.control_name}</p>
                        {c.d_statements[0] && (
                          <p className="text-xs text-[var(--muted)] mt-1 line-clamp-1">
                            {c.d_statements[0].text}
                          </p>
                        )}
                      </div>
                    </div>
                    <motion.div
                      className="text-[var(--muted)]"
                      whileHover={{ x: 2 }}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </motion.div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}
    </motion.div>
  );
}
