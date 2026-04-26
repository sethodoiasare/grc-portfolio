"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Search } from "lucide-react";

interface Market {
  id: number;
  name: string;
}

interface Props {
  value: Market | null;
  onChange: (market: Market | null) => void;
}

export function MarketSelector({ value, onChange }: Props) {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/v1/markets")
      .then((r) => r.json())
      .then(setMarkets)
      .catch(() => {});
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

  const filtered = query
    ? markets.filter((m) => m.name.toLowerCase().includes(query.toLowerCase()))
    : markets;

  return (
    <div ref={containerRef} className="market-selector">
      <button
        type="button"
        className="market-selector-trigger"
        onClick={() => setOpen(!open)}
      >
        <span className={value ? "market-selector-value" : "market-selector-placeholder"}>
          {value ? value.name : "Select a market..."}
        </span>
        <ChevronDown size={16} className={`market-selector-chevron ${open ? "open" : ""}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            className="market-selector-dropdown"
            initial={{ opacity: 0, y: -4, scaleY: 0.95 }}
            animate={{ opacity: 1, y: 0, scaleY: 1 }}
            exit={{ opacity: 0, y: -4, scaleY: 0.95 }}
            transition={{ duration: 0.15 }}
          >
            <div className="market-selector-search">
              <Search size={14} />
              <input
                type="text"
                placeholder="Search markets..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                autoFocus
              />
            </div>
            <div className="market-selector-list">
              {filtered.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  className={`market-selector-option ${value?.id === m.id ? "selected" : ""}`}
                  onClick={() => {
                    onChange(m);
                    setOpen(false);
                    setQuery("");
                  }}
                >
                  {m.name}
                </button>
              ))}
              {filtered.length === 0 && (
                <div className="market-selector-empty">No markets found</div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
