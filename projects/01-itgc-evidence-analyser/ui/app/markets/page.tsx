"use client";

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Trash2,
  Edit3,
  Check,
  X,
  Globe,
  Search,
  Building2,
  MapPin,
  Sparkles,
} from "lucide-react";
import { useAuth } from "../_hooks/useAuth";

interface Market {
  id: number;
  name: string;
  created_at: string;
}

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.035, delayChildren: 0.05 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 400, damping: 30 } },
};

function getRegion(market: string): string {
  if (["Albania", "Czech Republic", "Germany", "Greece", "Ireland", "Italy", "Netherlands", "Portugal", "Romania", "Spain", "Turkey"].includes(market)) return "Europe";
  if (["DRC", "Egypt", "Kenya", "Lesotho", "Mozambique", "South Africa", "Tanzania"].includes(market)) return "Africa";
  if (["Vodafone Automotive", "Vodafone Networks", "VBIT", "VSSI", "VSSB", "VSSR", "VSSE", "VFS", "GDC", "Global Cyber Security", "IoT", "Lowi", "MPesa Africa", "Office IT"].includes(market)) return "Group / Global";
  return "Europe";
}

const regionColors: Record<string, string> = {
  Europe: "#5b8def",
  Africa: "#f5a623",
  "Group / Global": "#26c963",
};

function SkeletonRow() {
  return (
    <div className="glass p-4 flex items-center gap-4">
      <div className="skeleton w-9 h-9 rounded-lg" />
      <div className="flex-1 space-y-2">
        <div className="skeleton w-32 h-3.5 rounded" />
        <div className="skeleton w-20 h-2.5 rounded" />
      </div>
    </div>
  );
}

export default function MarketsPage() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [newName, setNewName] = useState("");
  const [editing, setEditing] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const { token, user } = useAuth();
  const isAdmin = user?.role === "admin";

  useEffect(() => {
    fetch("/api/v1/markets")
      .then((r) => r.json())
      .then(setMarkets)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        const el = document.querySelector<HTMLInputElement>("#market-search");
        el?.focus();
      }
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return markets;
    const q = search.toLowerCase();
    return markets.filter((m) => m.name.toLowerCase().includes(q));
  }, [markets, search]);

  const regions = useMemo(() => {
    const map = new Map<string, number>();
    markets.forEach((m) => {
      const r = getRegion(m.name);
      map.set(r, (map.get(r) || 0) + 1);
    });
    return Array.from(map.entries()).sort((a, b) => b[1] - a[1]);
  }, [markets]);

  async function addMarket() {
    if (!newName.trim()) return;
    setError("");
    const res = await fetch("/api/v1/markets", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ name: newName.trim() }),
    });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      setError((d as { detail?: string }).detail || "Failed to add market");
      return;
    }
    const created = await res.json();
    setMarkets((prev) => [...prev, created].sort((a, b) => a.name.localeCompare(b.name)));
    setNewName("");
  }

  async function removeMarket(id: number) {
    await fetch(`/api/v1/markets/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    setMarkets((prev) => prev.filter((m) => m.id !== id));
    setConfirmDelete(null);
  }

  async function saveRename(id: number) {
    if (!editName.trim()) return;
    const res = await fetch(`/api/v1/markets/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ name: editName.trim() }),
    });
    if (res.ok) {
      const updated = await res.json();
      setMarkets((prev) =>
        prev.map((m) => (m.id === id ? updated : m)).sort((a, b) => a.name.localeCompare(b.name))
      );
    }
    setEditing(null);
  }

  return (
    <motion.div
      className="max-w-6xl mx-auto px-6 py-10"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Header */}
      <motion.div variants={item} className="mb-10">
        <div className="flex items-start justify-between gap-8">
          <div>
            <motion.div
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-4"
              style={{ background: "rgba(230, 0, 0, 0.08)", color: "#E60000", border: "1px solid rgba(230, 0, 0, 0.15)" }}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1, type: "spring", stiffness: 500 }}
            >
              <Globe className="w-3 h-3" />
              Vodafone Subsidiaries
            </motion.div>
            <h1 className="text-4xl font-bold tracking-[-0.03em] text-[var(--fg)] leading-tight">
              Markets
              <br />
              <span className="text-[var(--muted)]">Directory</span>
            </h1>
            <p className="text-sm text-[var(--muted)] mt-3 max-w-md leading-relaxed">
              {markets.length} markets across Vodafone operating companies and group entities.
              Each market is assessed against 58 ITGC controls.
            </p>
          </div>

          {/* Region breakdown */}
          {!loading && regions.length > 0 && (
            <motion.div
              className="hidden md:flex items-center gap-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              {regions.map(([region, count]) => (
                <div key={region} className="text-center">
                  <div className="text-2xl font-bold tracking-[-0.02em] text-[var(--fg)]">
                    {count}
                  </div>
                  <div className="flex items-center gap-1.5 mt-1">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ background: regionColors[region] || "var(--muted)" }}
                    />
                    <span className="text-xs text-[var(--muted)]">{region}</span>
                  </div>
                </div>
              ))}
            </motion.div>
          )}
        </div>
      </motion.div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            className="mb-6 px-4 py-3 rounded-lg text-sm font-medium"
            style={{ background: "rgba(240, 68, 68, 0.08)", border: "1px solid rgba(240, 68, 68, 0.2)", color: "var(--fail)" }}
            initial={{ opacity: 0, height: 0, marginBottom: 0 }}
            animate={{ opacity: 1, height: "auto", marginBottom: 24 }}
            exit={{ opacity: 0, height: 0, marginBottom: 0 }}
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toolbar: search + add */}
      <motion.div variants={item} className="flex items-center gap-3 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)] w-4 h-4" />
          <input
            id="market-search"
            type="text"
            placeholder="Search markets... (⌘K)"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] placeholder:text-[var(--muted)]/50 outline-none focus:border-[var(--accent)] transition-colors duration-200"
          />
          {search && (
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)] hover:text-[var(--fg)]"
              onClick={() => setSearch("")}
            >
              <X size={14} />
            </button>
          )}
        </div>

        {isAdmin && (
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Add market..."
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addMarket()}
              className="w-48 px-3 py-2.5 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] placeholder:text-[var(--muted)]/50 outline-none focus:border-[var(--accent)] transition-colors duration-200"
            />
            <button
              type="button"
              onClick={addMarket}
              disabled={!newName.trim()}
              className="flex items-center gap-1.5 px-4 py-2.5 bg-[var(--accent)] text-white rounded-lg text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[var(--accent-soft)] transition-colors duration-150"
            >
              <Plus size={16} />
              Add
            </button>
          </div>
        )}
      </motion.div>

      {/* Results count */}
      {search && (
        <motion.p
          className="text-xs text-[var(--muted)] mb-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {filtered.length} market{filtered.length !== 1 ? "s" : ""} matching &quot;{search}&quot;
        </motion.p>
      )}

      {/* Market list */}
      <motion.div variants={item} className="space-y-2">
        {loading ? (
          [1, 2, 3, 4, 5].map((i) => <SkeletonRow key={i} />)
        ) : filtered.length === 0 ? (
          <motion.div
            className="text-center py-20"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Globe size={40} className="mx-auto mb-4 text-[var(--muted)]/30" />
            <p className="text-[var(--muted)] text-sm">
              {search ? "No markets match your search." : "No markets found."}
            </p>
            {search && (
              <button
                type="button"
                onClick={() => setSearch("")}
                className="mt-2 text-xs text-[var(--accent)] hover:underline"
              >
                Clear search
              </button>
            )}
          </motion.div>
        ) : (
          filtered.map((m, i) => {
            const region = getRegion(m.name);
            const regionColor = regionColors[region] || "var(--muted)";

            return (
              <motion.div
                key={m.id}
                variants={item}
                custom={i}
                className="group glass p-4 flex items-center gap-4 hover:bg-[var(--surface-hover)]/50 transition-colors duration-200"
                style={{ borderRadius: "0.75rem" }}
                whileHover={{ scale: 1.005 }}
              >
                {/* Icon */}
                <div
                  className="flex items-center justify-center w-9 h-9 rounded-lg flex-shrink-0"
                  style={{ background: `${regionColor}12`, border: `1px solid ${regionColor}22` }}
                >
                  <Building2 size={16} style={{ color: regionColor }} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  {editing === m.id ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") saveRename(m.id);
                          if (e.key === "Escape") setEditing(null);
                        }}
                        className="flex-1 px-2.5 py-1 bg-[var(--surface)] border border-[var(--accent)] rounded text-sm text-[var(--fg)] outline-none"
                        autoFocus
                      />
                      <button
                        type="button"
                        onClick={() => saveRename(m.id)}
                        className="p-1.5 rounded hover:bg-[var(--pass)]/10 text-[var(--pass)] transition-colors"
                      >
                        <Check size={15} />
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditing(null)}
                        className="p-1.5 rounded hover:bg-[var(--fail)]/10 text-[var(--fail)] transition-colors"
                      >
                        <X size={15} />
                      </button>
                    </div>
                  ) : (
                    <>
                      <span className="text-sm font-semibold text-[var(--fg)] truncate block">
                        {m.name}
                      </span>
                      <div className="flex items-center gap-2 mt-0.5">
                        <div className="flex items-center gap-1">
                          <MapPin size={10} className="text-[var(--muted)]" />
                          <span className="text-xs text-[var(--muted)]">{region}</span>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Actions */}
                {isAdmin && editing !== m.id && (
                  <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-150">
                    <button
                      type="button"
                      onClick={() => {
                        setEditing(m.id);
                        setEditName(m.name);
                      }}
                      className="p-1.5 rounded-md hover:bg-[var(--surface-elevated)] text-[var(--muted)] hover:text-[var(--fg)] transition-colors"
                      title="Rename"
                    >
                      <Edit3 size={14} />
                    </button>
                    {confirmDelete === m.id ? (
                      <div className="flex items-center gap-0.5">
                        <button
                          type="button"
                          onClick={() => removeMarket(m.id)}
                          className="px-2 py-1 rounded text-xs font-medium bg-[var(--fail)]/10 text-[var(--fail)] hover:bg-[var(--fail)]/20 transition-colors"
                        >
                          Delete
                        </button>
                        <button
                          type="button"
                          onClick={() => setConfirmDelete(null)}
                          className="p-1 rounded-md text-[var(--muted)] hover:text-[var(--fg)]"
                        >
                          <X size={13} />
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setConfirmDelete(m.id)}
                        className="p-1.5 rounded-md hover:bg-[var(--fail)]/10 text-[var(--muted)] hover:text-[var(--fail)] transition-colors"
                        title="Delete"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                )}
              </motion.div>
            );
          })
        )}
      </motion.div>
    </motion.div>
  );
}
