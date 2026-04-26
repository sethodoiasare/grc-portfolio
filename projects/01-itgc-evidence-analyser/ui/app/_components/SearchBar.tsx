"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SearchResult {
  type: "control" | "market";
  id: string;
  title: string;
  subtitle: string;
  href: string;
}

interface Props {
  className?: string;
}

export function SearchBar({ className = "" }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen(true);
        setTimeout(() => inputRef.current?.focus(), 100);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  useEffect(() => {
    if (query.length < 1) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        const items: SearchResult[] = [];
        for (const c of data.controls || []) {
          items.push({
            type: "control",
            id: c.control_id,
            title: c.control_name,
            subtitle: c.control_id + " · " + (c.domain || ""),
            href: `/controls/${c.control_id}`,
          });
        }
        for (const m of data.markets || []) {
          items.push({
            type: "market",
            id: String(m.id),
            title: m.name,
            subtitle: "Market",
            href: `/assess?market_id=${m.id}`,
          });
        }
        setResults(items.slice(0, 10));
        setSelected(0);
      } catch {}
    }, 200);
    return () => clearTimeout(timer);
  }, [query]);

  function navigate(result: SearchResult) {
    setOpen(false);
    setQuery("");
    router.push(result.href);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelected((s) => Math.min(s + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelected((s) => Math.max(s - 1, 0));
    } else if (e.key === "Enter" && results[selected]) {
      navigate(results[selected]);
    }
  }

  return (
    <div ref={containerRef} className={`search-bar-wrapper ${className}`}>
      <button
        type="button"
        className="search-bar-trigger"
        onClick={() => {
          setOpen(true);
          setTimeout(() => inputRef.current?.focus(), 100);
        }}
      >
        <Search size={16} />
        <span>Search controls & markets...</span>
        <kbd className="search-bar-kbd">⌘K</kbd>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            className="search-bar-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.1 }}
          >
            <motion.div
              className="search-bar-panel"
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.15 }}
            >
              <div className="search-bar-input-row">
                <Search size={18} className="search-bar-input-icon" />
                <input
                  ref={inputRef}
                  type="text"
                  placeholder="Search controls and markets..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <button
                  type="button"
                  className="search-bar-close"
                  onClick={() => setOpen(false)}
                >
                  <X size={18} />
                </button>
              </div>

              {results.length > 0 && (
                <div className="search-bar-results">
                  {results.map((r, i) => (
                    <button
                      key={r.type + r.id}
                      type="button"
                      className={`search-bar-result ${i === selected ? "selected" : ""}`}
                      onClick={() => navigate(r)}
                      onMouseEnter={() => setSelected(i)}
                    >
                      <div className="search-bar-result-type">
                        {r.type === "control" ? "Control" : "Market"}
                      </div>
                      <div className="search-bar-result-title">{r.title}</div>
                      <div className="search-bar-result-sub">{r.subtitle}</div>
                    </button>
                  ))}
                </div>
              )}

              {query && results.length === 0 && (
                <div className="search-bar-empty">No results found</div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
