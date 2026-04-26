"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Shield, ArrowLeft, FileText, CheckSquare, ExternalLink } from "lucide-react";

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

export default function ControlDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [control, setControl] = useState<Control | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/controls/${id}`)
      .then((r) => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then(setControl)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="glass p-12 text-center">
          <div className="w-8 h-8 mx-auto mb-4 border-2 border-[var(--accent)]/30 border-t-[var(--accent)] rounded-full animate-spin" />
          <p className="text-sm text-[var(--muted)]">Loading control...</p>
        </div>
      </div>
    );
  }

  if (error || !control) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="glass p-12 text-center">
          <Shield className="w-8 h-8 mx-auto mb-3 text-[var(--muted)]/40" />
          <p className="text-sm text-[var(--muted)]">Control not found</p>
          <Link href="/controls" className="text-sm text-[var(--accent)] hover:underline mt-2 inline-block">
            Back to controls
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Breadcrumb */}
      <Link
        href="/controls"
        className="inline-flex items-center gap-1.5 text-xs text-[var(--muted)] hover:text-[var(--fg)] mb-6 transition-colors"
      >
        <ArrowLeft className="w-3 h-3" /> Controls
      </Link>

      {/* Header */}
      <div className="glass p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="font-mono text-sm text-[var(--accent)] font-bold">{control.control_id}</span>
              <span className="px-2 py-0.5 text-[10px] rounded-md bg-[var(--accent)]/10 text-[var(--accent)] font-semibold">
                {control.domain}
              </span>
            </div>
            <h1 className="text-xl font-bold text-[var(--fg)]">{control.control_name}</h1>
          </div>
          <Link
            href={`/assess?control=${control.control_id}`}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white text-sm font-medium rounded-lg hover:bg-[var(--accent)]/90 transition-colors"
          >
            <CheckSquare className="w-4 h-4" />
            Assess
          </Link>
        </div>
      </div>

      {/* Statements */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Design Statements (D) */}
        <div className="glass p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 rounded bg-blue-500/10 flex items-center justify-center">
              <FileText className="w-3.5 h-3.5 text-blue-400" />
            </div>
            <h2 className="text-sm font-semibold text-[var(--fg)]">Design Statements (D)</h2>
            <span className="text-[10px] text-[var(--muted)] ml-auto">{control.d_statements.length} items</span>
          </div>
          <ul className="space-y-3">
            {control.d_statements.map((s, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="font-mono text-xs text-blue-400 mt-0.5 flex-shrink-0">{s.id}</span>
                <span className="text-[var(--fg)]/85 leading-relaxed">{s.text}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Evidence Statements (E) */}
        <div className="glass p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 rounded bg-purple-500/10 flex items-center justify-center">
              <ExternalLink className="w-3.5 h-3.5 text-purple-400" />
            </div>
            <h2 className="text-sm font-semibold text-[var(--fg)]">Evidence Statements (E)</h2>
            <span className="text-[10px] text-[var(--muted)] ml-auto">{control.e_statements.length} items</span>
          </div>
          <ul className="space-y-3">
            {control.e_statements.map((s, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="font-mono text-xs text-purple-400 mt-0.5 flex-shrink-0">{s.id}</span>
                <span className="text-[var(--fg)]/85 leading-relaxed">{s.text}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Assessment link */}
      <div className="mt-6 glass glass-hover p-5 text-center">
        <p className="text-sm text-[var(--muted)]">
          Ready to assess evidence against this control?
        </p>
        <Link
          href={`/assess?control=${control.control_id}`}
          className="inline-flex items-center gap-2 mt-2 px-5 py-2.5 bg-[var(--accent)] text-white text-sm font-medium rounded-lg hover:bg-[var(--accent)]/90 transition-colors"
        >
          <CheckSquare className="w-4 h-4" />
          Run Assessment for {control.control_id}
        </Link>
      </div>
    </div>
  );
}
