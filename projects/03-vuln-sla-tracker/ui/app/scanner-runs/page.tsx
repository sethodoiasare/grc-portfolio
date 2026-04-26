"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Upload, FileText, BarChart3, CheckCircle } from "lucide-react";

interface ScannerRun {
  id: number; scanner_type: string; filename: string;
  vulns_imported: number; vulns_new: number; vulns_updated: number;
  imported_at: string;
}

export default function ScannerRunsPage() {
  const [runs, setRuns] = useState<ScannerRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  async function loadRuns() {
    const res = await fetch("/api/v1/scanner/runs");
    if (res.ok) setRuns(await res.json());
    setLoading(false);
  }

  useEffect(() => { loadRuns(); }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setMessage("");

    const form = new FormData();
    form.append("file", file);

    const token = localStorage.getItem("itgc_token");
    const scannerType = file.name.toLowerCase().includes("nessus") ? "nessus"
      : file.name.toLowerCase().includes("openvas") ? "openvas" : "qualys";

    const res = await fetch(`/api/v1/scanner/import?scanner_type=${scannerType}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });

    if (res.ok) {
      const data = await res.json();
      setMessage(`Imported ${data.vulns_imported} vulns (${data.vulns_new} new, ${data.vulns_updated} updated)`);
      loadRuns();
    } else {
      const err = await res.json().catch(() => ({}));
      setMessage((err as { detail?: string }).detail || "Upload failed");
    }
    setUploading(false);
    e.target.value = "";
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-[var(--fg)] mb-1">Scanner Runs</h1>
            <p className="text-sm text-[var(--muted)]">{runs.length} import runs</p>
          </div>
          <label className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg text-sm font-medium cursor-pointer hover:bg-[var(--accent-soft)] transition-colors">
            <Upload size={15} />
            {uploading ? "Uploading..." : "Import Scanner CSV"}
            <input type="file" accept=".csv" onChange={handleUpload} className="hidden" disabled={uploading} />
          </label>
        </div>

        {message && (
          <motion.div
            className="mb-4 p-3 rounded-lg text-sm border"
            style={{
              backgroundColor: message.includes("failed") ? "rgba(240,68,68,0.1)" : "rgba(38,201,99,0.1)",
              borderColor: message.includes("failed") ? "rgba(240,68,68,0.25)" : "rgba(38,201,99,0.25)",
              color: message.includes("failed") ? "var(--fail)" : "var(--pass)",
            }}
            initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
          >
            {message}
          </motion.div>
        )}
      </motion.div>

      <div className="glass overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-left text-xs text-[var(--muted)]">
                <th className="py-3 px-4 font-medium">ID</th>
                <th className="py-3 px-4 font-medium">Scanner</th>
                <th className="py-3 px-4 font-medium">Filename</th>
                <th className="py-3 px-4 font-medium">Imported</th>
                <th className="py-3 px-4 font-medium">New</th>
                <th className="py-3 px-4 font-medium">Updated</th>
                <th className="py-3 px-4 font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {loading && [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-[var(--border)]/30"><td colSpan={7} className="py-4 px-4"><div className="skeleton h-6 w-full" /></td></tr>
              ))}
              {!loading && runs.map((r) => (
                <tr key={r.id} className="border-b border-[var(--border)]/30 hover:bg-[var(--surface-hover)]/50 transition-colors">
                  <td className="py-3 px-4 font-mono text-xs text-[var(--muted)]">#{r.id}</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[var(--accent)]/10 text-[var(--accent)] capitalize">{r.scanner_type}</span>
                  </td>
                  <td className="py-3 px-4 text-[var(--fg)]">
                    <div className="flex items-center gap-1.5"><FileText size={14} className="text-[var(--muted)]" />{r.filename}</div>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-[var(--fg)]">{r.vulns_imported}</td>
                  <td className="py-3 px-4 font-mono text-xs text-[var(--pass)]">{r.vulns_new}</td>
                  <td className="py-3 px-4 font-mono text-xs text-[var(--accent)]">{r.vulns_updated}</td>
                  <td className="py-3 px-4 text-xs text-[var(--muted)]">{r.imported_at?.slice(0, 16).replace("T", " ")}</td>
                </tr>
              ))}
              {!loading && runs.length === 0 && (
                <tr><td colSpan={7} className="py-12 text-center text-[var(--muted)]">No scanner runs yet. Import a CSV to get started.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
