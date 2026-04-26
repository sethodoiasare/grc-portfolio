"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, Search, ClipboardCheck, Activity } from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: Activity },
  { href: "/controls", label: "Controls", icon: Search },
  { href: "/assess", label: "Assess", icon: ClipboardCheck },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 h-full flex-shrink-0 border-r border-[var(--border)] bg-[var(--surface)] flex flex-col">
      {/* Brand */}
      <div className="h-14 flex items-center gap-3 px-5 border-b border-[var(--border)]">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[var(--accent)]/10 ring-1 ring-[var(--accent)]/25">
          <Shield className="w-4 h-4 text-[var(--accent)]" />
        </div>
        <Link href="/" className="text-sm font-semibold tracking-tight text-[var(--fg)]">
          ITGC Analyser
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 text-sm rounded-lg transition-all duration-200 ${
                active
                  ? "bg-[var(--accent)]/10 text-[var(--accent)] font-medium ring-1 ring-[var(--accent)]/20"
                  : "text-[var(--muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--fg)]"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-[var(--border)]">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--pass)] animate-pulse" />
          <span className="text-xs text-[var(--muted)]">API Connected</span>
        </div>
        <p className="text-[10px] text-[var(--muted)]/60 mt-1">Vodafone ITGC v1.0</p>
      </div>
    </aside>
  );
}
