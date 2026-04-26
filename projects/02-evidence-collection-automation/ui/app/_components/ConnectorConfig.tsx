"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Settings, CheckCircle, XCircle, Loader2, Zap, Globe, Shield } from "lucide-react";
import { useAuth } from "../_hooks/useAuth";

interface FieldSchema {
  name: string;
  type: string;
  label: string;
  default: string | number;
}

interface Props {
  connectorId: number;
  connectorName: string;
  connectorType: string;
  mode: string;
  authConfig: Record<string, unknown>;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export function ConnectorConfig({ connectorId, connectorName, connectorType, mode, authConfig, open, onClose, onSaved }: Props) {
  const [schema, setSchema] = useState<{ fields: FieldSchema[]; integration_types: string[]; required_fields: Record<string, string[]> } | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [integrationType, setIntegrationType] = useState<string>("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; detail?: string; error?: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    if (!open) return;
    fetch(`/api/v1/connectors/${connectorId}/schema`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(s => {
        setSchema(s);
        const vals: Record<string, string> = {};
        s.fields.forEach((f: FieldSchema) => {
          vals[f.name] = authConfig[f.name] ? String(authConfig[f.name]) : String(f.default);
        });
        setFormValues(vals);
        setIntegrationType(authConfig.integration_type as string || s.integration_types?.[0] || "");
        setTestResult(null);
        setMessage(null);
      });
  }, [open, connectorId, token, authConfig]);

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      // Switch to live mode first if not already
      if (mode !== "live") {
        await fetch(`/api/v1/connectors/${connectorId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({ mode: "live" }),
        });
        // Small delay to ensure mode switch is picked up
        await new Promise(r => setTimeout(r, 300));
      }
      const res = await fetch(`/api/v1/connectors/${connectorId}/test`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      setTestResult(await res.json());
    } catch {
      setTestResult({ ok: false, error: "Network error testing connection" });
    }
    setTesting(false);
  }

  async function handleSave() {
    setSaving(true);
    setMessage(null);
    try {
      const config: Record<string, unknown> = { ...formValues, integration_type: integrationType };
      // Convert port to number
      if (config.port) config.port = Number(config.port);
      await fetch(`/api/v1/connectors/${connectorId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ auth_config: config }),
      });
      setMessage("Configuration saved");
      setTimeout(() => { onSaved(); onClose(); }, 800);
    } catch {
      setMessage("Failed to save configuration");
    }
    setSaving(false);
  }

  const requiredFields = integrationType && schema?.required_fields?.[integrationType] ? schema.required_fields[integrationType] : [];
  const visibleFields = (schema?.fields || []).filter(f => {
    if (f.name === "integration_type") return false;
    // Only show fields relevant to the selected integration type
    const intFields: Record<string, string[]> = {
      azure_ad: ["tenant_id", "client_id", "client_secret"],
      on_prem_ad: ["domain", "ldap_server", "base_dn"],
      ldap: ["ldap_server", "base_dn"],
      intune: ["tenant_id", "client_id", "client_secret"],
      workspace_one: ["workspace_one_url", "workspace_one_api_key"],
      panorama: ["host", "port", "api_key", "vendor"],
      checkpoint_mgmt: ["host", "port", "api_key", "vendor"],
      fortimanager: ["host", "port", "api_key", "vendor"],
      ssh: ["host", "port", "username", "password", "vendor"],
      tenable: ["api_url", "access_key", "secret_key"],
      qualys: ["api_url", "access_key", "secret_key"],
      rapid7: ["api_url", "access_key", "secret_key"],
      openvas: ["api_url", "access_key", "secret_key"],
      sentinel: ["workspace_id", "tenant_id", "client_id", "client_secret"],
      splunk: ["splunk_host", "splunk_token"],
      qradar: ["splunk_host", "splunk_token"],
      elastic: ["splunk_host", "splunk_token"],
      purview: ["tenant_id", "client_id", "client_secret"],
      symantec: ["symantec_api_url", "symantec_api_key"],
      forcepoint: ["symantec_api_url", "symantec_api_key"],
    };
    const relevant = intFields[integrationType] || [];
    return relevant.includes(f.name);
  });

  return (
    <AnimatePresence>
      {open && (
        <>
          <div className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />
          <motion.div
            className="fixed inset-y-0 right-0 w-[480px] max-w-[90vw] z-50 bg-[var(--surface)] border-l border-[var(--border)] shadow-2xl overflow-y-auto"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            {/* Header */}
            <div className="sticky top-0 z-10 bg-[var(--surface)]/95 backdrop-blur-sm border-b border-[var(--border)] p-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Settings size={16} className="text-[var(--accent)]" />
                    <h2 className="text-lg font-bold text-[var(--fg)]">{connectorName}</h2>
                  </div>
                  <p className="text-xs text-[var(--muted)]">Live Integration Configuration</p>
                </div>
                <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-[var(--surface-hover)] text-[var(--muted)]">
                  <X size={18} />
                </button>
              </div>
            </div>

            <div className="p-5 space-y-5">
              {/* Integration Type Selector */}
              {schema?.integration_types && schema.integration_types.length > 1 && (
                <div>
                  <label className="text-xs font-medium text-[var(--muted)] uppercase mb-2 block">Integration Target</label>
                  <select
                    value={integrationType}
                    onChange={e => setIntegrationType(e.target.value)}
                    className="w-full px-3 py-2.5 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] outline-none focus:border-[var(--accent)]"
                  >
                    {schema.integration_types.map((t: string) => (
                      <option key={t} value={t}>{t.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Form Fields */}
              <div className="space-y-3">
                {visibleFields.map(f => (
                  <div key={f.name}>
                    <label className="text-xs font-medium text-[var(--muted)] mb-1.5 block">
                      {f.label}
                      {requiredFields.includes(f.name) && <span className="text-[var(--fail)] ml-1">*</span>}
                    </label>
                    <input
                      type={f.type}
                      value={formValues[f.name] || ""}
                      onChange={e => setFormValues(prev => ({ ...prev, [f.name]: e.target.value }))}
                      placeholder={f.label}
                      className="w-full px-3 py-2 bg-[var(--surface-hover)] border border-[var(--border)] rounded-lg text-sm text-[var(--fg)] placeholder:text-[var(--muted)]/40 outline-none focus:border-[var(--accent)] font-mono"
                    />
                  </div>
                ))}
              </div>

              {/* Test Connection */}
              <div className="p-4 rounded-lg bg-[var(--surface-hover)]/50 border border-[var(--border)]/50">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    testResult?.ok ? "bg-[var(--pass)]/10" : testResult && !testResult.ok ? "bg-[var(--fail)]/10" : "bg-[var(--surface-hover)]"
                  }`}>
                    {testing ? <Loader2 size={16} className="animate-spin text-[var(--accent)]" /> :
                     testResult?.ok ? <CheckCircle size={16} className="text-[var(--pass)]" /> :
                     testResult ? <XCircle size={16} className="text-[var(--fail)]" /> :
                     <Globe size={16} className="text-[var(--muted)]" />}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[var(--fg)]">Test Connection</p>
                    <p className="text-[10px] text-[var(--muted)]">Verify the connector can reach the target system</p>
                  </div>
                </div>

                {testResult && (
                  <div className={`mb-3 p-3 rounded-lg text-xs ${
                    testResult.ok ? "bg-[var(--pass)]/5 border border-[var(--pass)]/20 text-[var(--pass)]" :
                    "bg-[var(--fail)]/5 border border-[var(--fail)]/20 text-[var(--fail)]"
                  }`}>
                    {testResult.ok ? testResult.detail || "Connection successful" : testResult.error}
                  </div>
                )}

                <button
                  onClick={handleTest}
                  disabled={testing}
                  className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)]/10 text-[var(--accent)] rounded-lg text-sm font-semibold hover:bg-[var(--accent)]/20 disabled:opacity-40 transition-colors"
                >
                  {testing ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
                  {testing ? "Testing..." : "Test Connection"}
                </button>
              </div>

              {/* Security Note */}
              <div className="flex items-start gap-2 p-3 rounded-lg bg-[var(--partial)]/5 border border-[var(--partial)]/20">
                <Shield size={14} className="text-[var(--partial)] mt-0.5 flex-shrink-0" />
                <p className="text-[10px] text-[var(--muted)]">
                  Credentials are stored in the local database. In production, use Azure Key Vault or HashiCorp Vault for secret management. Network access to Vodafone systems (VPN/jump host) is required for live connections.
                </p>
              </div>

              {/* Message */}
              {message && (
                <div className={`p-3 rounded-lg text-xs text-center ${message.includes("Failed") ? "bg-[var(--fail)]/10 text-[var(--fail)]" : "bg-[var(--pass)]/10 text-[var(--pass)]"}`}>
                  {message}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2.5 border border-[var(--border)] rounded-lg text-sm text-[var(--muted)] hover:text-[var(--fg)] transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-[var(--accent)] text-white rounded-lg text-sm font-semibold hover:bg-[var(--accent-soft)] disabled:opacity-40 transition-colors"
                >
                  {saving ? "Saving..." : "Save Configuration"}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
