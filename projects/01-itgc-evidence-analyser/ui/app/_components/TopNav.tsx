"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Shield, Search, ClipboardCheck, Activity, FileText, Globe, LogOut } from "lucide-react";
import { SearchBar } from "./SearchBar";
import { ChatWidget } from "./ChatWidget";
import { useAuth } from "../_hooks/useAuth";

export function TopNav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navItems = [
    { href: "/", label: "Dashboard", icon: Activity },
    { href: "/controls", label: "Controls", icon: Search },
    { href: "/assess", label: "Assess", icon: ClipboardCheck },
    { href: "/assessments", label: "Assessments", icon: FileText },
  ];

  if (user?.role === "admin") {
    navItems.push({ href: "/markets", label: "Markets", icon: Globe });
  }

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg)]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.97 }}
              className="flex items-center justify-center w-8 h-8 rounded-lg bg-[var(--accent)]/10 ring-1 ring-[var(--accent)]/25"
            >
              <Shield className="w-4 h-4 text-[var(--accent)]" />
            </motion.div>
            <span className="text-sm font-semibold tracking-tight text-[var(--fg)]">
              ITGC Analyser
            </span>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {navItems.map(({ href, label, icon: Icon }) => {
              const active = pathname === href || (href !== "/" && pathname.startsWith(href));
              return (
                <Link key={href} href={href} className="relative px-3 py-1.5">
                  <motion.span
                    className={`relative z-10 flex items-center gap-2 text-sm rounded-md transition-colors duration-200 ${
                      active
                        ? "text-[var(--fg)] font-medium"
                        : "text-[var(--muted)] hover:text-[var(--fg)]"
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.97 }}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {label}
                  </motion.span>
                  {active && (
                    <motion.div
                      layoutId="nav-pill"
                      className="absolute inset-0 rounded-md bg-[var(--accent)]/10 ring-1 ring-[var(--accent)]/15"
                      transition={{ type: "spring", stiffness: 500, damping: 35 }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Right section */}
          <div className="flex items-center gap-3">
            <SearchBar />
            {user && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--muted)] max-w-[120px] truncate">
                  {user.email}
                </span>
                <button
                  type="button"
                  onClick={logout}
                  className="flex items-center gap-1 text-xs text-[var(--muted)] hover:text-[var(--fg)] transition-colors"
                  title="Sign out"
                >
                  <LogOut size={14} />
                </button>
              </div>
            )}
          </div>
        </div>
      </header>
      <ChatWidget />
    </>
  );
}
