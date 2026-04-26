// @ts-nocheck
"use client";

// Renders evidence data as readable tables/cards instead of raw JSON

function KeyValue({ label, value }: { label: string; value: unknown }) {
  if (value === null || value === undefined || value === "") return null;
  const display = typeof value === "object" ? JSON.stringify(value) : String(value);
  return (
    <div className="flex justify-between py-1.5 border-b border-[var(--border)]/50">
      <span className="text-xs text-[var(--muted)]">{label}</span>
      <span className="text-xs text-[var(--fg)] font-medium text-right max-w-[60%] truncate">{display}</span>
    </div>
  );
}

function UserTable({ users }: { users: Record<string, unknown>[] }) {
  if (!users?.length) return null;
  const cols = Object.keys(users[0]).filter(k => !["member_of"].includes(k)).slice(0, 6);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[var(--border)]">
            {cols.map(c => <th key={c} className="text-left p-2 text-[var(--muted)] font-medium uppercase text-[10px]">{c.replace(/_/g, " ")}</th>)}
            <th className="text-left p-2 text-[var(--muted)] font-medium uppercase text-[10px]">groups</th>
          </tr>
        </thead>
        <tbody>
          {users.slice(0, 20).map((u, i) => (
            <tr key={i} className="border-b border-[var(--border)]/30 hover:bg-[var(--surface-hover)]/50">
              {cols.map(c => <td key={c} className="p-2 text-[var(--fg)]">{String(u[c] ?? "—")}</td>)}
              <td className="p-2 text-[var(--fg)]">{Array.isArray(u.member_of) ? (u.member_of as string[]).slice(0, 3).join(", ") : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {users.length > 20 && <p className="text-[10px] text-[var(--muted)] p-2">+ {users.length - 20} more users</p>}
    </div>
  );
}

function VulnerabilityCards({ vulnerabilities }: { vulnerabilities: Record<string, unknown>[] }) {
  if (!vulnerabilities?.length) return null;
  const severityColor: Record<string, string> = { CRITICAL: "var(--fail)", HIGH: "#f97316", MEDIUM: "var(--partial)", LOW: "var(--muted)" };
  return (
    <div className="space-y-2 max-h-96 overflow-y-auto">
      {vulnerabilities.map((v, i) => (
        <div key={i} className="p-3 rounded-lg bg-[var(--surface-hover)]/50 border border-[var(--border)]/50">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] px-1.5 py-0.5 rounded font-bold" style={{ background: `${severityColor[String(v.severity)] || "var(--muted)"}18`, color: severityColor[String(v.severity)] || "var(--muted)" }}>
              {String(v.severity)}
            </span>
            <span className="text-xs font-semibold text-[var(--fg)]">{String(v.cve_id)}</span>
            <span className="text-[10px] text-[var(--muted)] ml-auto">CVSS {String(v.cvss_score)}</span>
          </div>
          <p className="text-xs text-[var(--fg)]">{String(v.title)}</p>
          <div className="flex gap-3 mt-1 text-[10px] text-[var(--muted)]">
            <span>Asset: {String(v.affected_asset)}</span>
            <span>Patch: {v.patch_available ? "Available" : "Not available"}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function AlertTable({ alerts }: { alerts: Record<string, unknown>[] }) {
  if (!alerts?.length) return null;
  const severityColor: Record<string, string> = { CRITICAL: "var(--fail)", HIGH: "#f97316", MEDIUM: "var(--partial)", LOW: "var(--muted)" };
  return (
    <div className="space-y-1 max-h-96 overflow-y-auto">
      {alerts.slice(0, 25).map((a, i) => (
        <div key={i} className="flex items-center gap-3 p-2 rounded hover:bg-[var(--surface-hover)]/50">
          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: severityColor[String(a.severity)] || "var(--muted)" }} />
          <span className="text-xs text-[var(--fg)] flex-1 truncate">{String(a.type)}</span>
          <span className="text-[10px] text-[var(--muted)]">{String(a.status)}</span>
        </div>
      ))}
    </div>
  );
}

function DeviceTable({ devices }: { devices: Record<string, unknown>[] }) {
  if (!devices?.length) return null;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[var(--border)]">
            {["device_name", "make_model", "os_version", "enrollment_status", "encryption_enabled"].map(c => (
              <th key={c} className="text-left p-2 text-[var(--muted)] font-medium uppercase text-[10px]">{c.replace(/_/g, " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {devices.slice(0, 20).map((d, i) => (
            <tr key={i} className="border-b border-[var(--border)]/30 hover:bg-[var(--surface-hover)]/50">
              <td className="p-2 text-[var(--fg)]">{String(d.device_name)}</td>
              <td className="p-2 text-[var(--fg)]">{String(d.make_model)}</td>
              <td className="p-2 text-[var(--fg)]">{String(d.os_version)}</td>
              <td className="p-2">
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${d.enrollment_status === "compliant" ? "bg-[var(--pass)]/10 text-[var(--pass)]" : "bg-[var(--fail)]/10 text-[var(--fail)]"}`}>
                  {String(d.enrollment_status)}
                </span>
              </td>
              <td className="p-2">{d.encryption_enabled ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FirewallRules({ rules }: { rules: Record<string, unknown>[] }) {
  if (!rules?.length) return null;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[var(--border)]">
            {["rule_id", "name", "source", "destination", "service", "action", "log_enabled"].map(c => (
              <th key={c} className="text-left p-2 text-[var(--muted)] font-medium uppercase text-[10px]">{c.replace(/_/g, " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rules.slice(0, 20).map((r, i) => (
            <tr key={i} className="border-b border-[var(--border)]/30 hover:bg-[var(--surface-hover)]/50">
              <td className="p-2 text-[var(--muted)]">{String(r.rule_id)}</td>
              <td className="p-2 text-[var(--fg)]">{String(r.name)}</td>
              <td className="p-2 text-[var(--fg)]">{String(r.source)}</td>
              <td className="p-2 text-[var(--fg)]">{String(r.destination)}</td>
              <td className="p-2 text-[var(--fg)]">{String(r.service)}</td>
              <td className="p-2">
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${r.action === "allow" ? "bg-[var(--pass)]/10 text-[var(--pass)]" : "bg-[var(--fail)]/10 text-[var(--fail)]"}`}>
                  {String(r.action)}
                </span>
              </td>
              <td className="p-2">{r.log_enabled ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatGrid({ evidenceData }: { evidenceData: Record<string, unknown> }) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = evidenceData as Record<string, any>;
  const numericKeys = Object.entries(data).filter(([, v]) => typeof v === "number" || (typeof v === "string" && !isNaN(Number(v))));
  const skipKeys = ["note", "total_vulnerabilities", "total_devices", "total_users", "total_rules", "total_alerts", "user_count", "vulnerabilities", "users", "devices", "rules", "alerts", "events", "privileged_groups", "mfa_methods", "enrollment_methods", "ios_versions", "android_versions", "windows_versions", "by_severity", "sources_by_type", "monitored_channels", "categories", "external_ports", "internal_ports"];
  const showKeys = numericKeys.filter(([k]) => !skipKeys.includes(k)).slice(0, 8);

  if (!showKeys.length) return null;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
      {showKeys.map(([k, v]) => (
        <div key={k} className="p-2 rounded bg-[var(--surface-hover)]">
          <p className="text-[10px] text-[var(--muted)] uppercase">{k.replace(/_/g, " ")}</p>
          <p className="text-lg font-bold text-[var(--fg)]">{v !== null && v !== undefined ? String(v) : "—"}</p>
        </div>
      ))}
    </div>
  );
}

function DistributionBar({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).filter(([, v]) => typeof v === "number");
  if (!entries.length || entries.length > 10) return null;
  const total = entries.reduce((s, [, v]) => s + v, 0);
  const colors = ["#5b8def", "#26c963", "#f5a623", "#f04444", "#6b7280", "#a78bfa", "#f97316", "#06b6d4"];
  return (
    <div className="mb-3">
      <div className="flex h-4 rounded overflow-hidden mb-1">
        {entries.map(([, v], i) => (
          <div key={i} style={{ width: `${(v / total) * 100}%`, background: colors[i % colors.length] }} />
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {entries.map(([k, v], i) => (
          <span key={k} className="text-[10px] flex items-center gap-1">
            <span className="w-2 h-2 rounded-full" style={{ background: colors[i % colors.length] }} />
            {k.replace(/_/g, " ")}: {v}
          </span>
        ))}
      </div>
    </div>
  );
}

interface Props {
  evidenceType: string;
  data: Record<string, unknown>;
}

export function EvidenceRenderer({ evidenceType, data }: Props) {
  const typedData: Record<string, unknown> = data || {};
  return (
    <div className="space-y-2">
      {/* Summary stats */}
      <StatGrid evidenceData={typedData} />

      {/* Distribution bars */}
      {(data.mfa_methods || data.enrollment_methods || data.by_severity || data.sources_by_type || data.ios_versions) && (
        <DistributionBar data={(data.by_severity || data.mfa_methods || data.enrollment_methods || data.sources_by_type || data.ios_versions || {}) as unknown as Record<string, number>} />
      )}

      {/* Type-specific tables */}
      {evidenceType === "user_list" && data.users && <UserTable users={data.users as Record<string, unknown>[]} />}
      {evidenceType === "device_compliance" && data.devices && <DeviceTable devices={data.devices as Record<string, unknown>[]} />}
      {evidenceType === "firewall_rules" && data.rules && <FirewallRules rules={data.rules as Record<string, unknown>[]} />}
      {evidenceType === "vulnerability_list" && data.vulnerabilities && <VulnerabilityCards vulnerabilities={data.vulnerabilities as Record<string, unknown>[]} />}
      {evidenceType === "alert_volume" && data.alerts && <AlertTable alerts={data.alerts as Record<string, unknown>[]} />}

      {/* Simple key-value for other types */}
      {!["user_list", "device_compliance", "firewall_rules", "vulnerability_list", "alert_volume"].includes(evidenceType) && (
        <div>
          {Object.entries(data).filter(([, v]) => typeof v !== "object" || v === null).slice(0, 10).map(([k, v]) => (
            <KeyValue key={k} label={k.replace(/_/g, " ")} value={v} />
          ))}
        </div>
      )}

      {/* Channel config */}
      {data.monitored_channels && (
        <div className="space-y-1">
          {(data.monitored_channels as Array<{name: string; status: string}>).map((ch, i) => (
            <div key={i} className="flex items-center justify-between p-2 rounded bg-[var(--surface-hover)]">
              <span className="text-xs text-[var(--fg)]">{ch.name}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                ch.status === "protected" ? "bg-[var(--pass)]/10 text-[var(--pass)]" :
                ch.status === "blocked" ? "bg-[var(--fail)]/10 text-[var(--fail)]" :
                "bg-[var(--partial)]/10 text-[var(--partial)]"
              }`}>{ch.status}</span>
            </div>
          ))}
        </div>
      )}

      {/* Privileged groups */}
      {data.privileged_groups && (
        <div className="space-y-1">
          {(data.privileged_groups as Array<{name: string; member_count: number; last_reviewed: string}>).map((g, i) => (
            <div key={i} className="flex items-center justify-between p-2 rounded bg-[var(--surface-hover)]">
              <span className="text-xs text-[var(--fg)]">{g.name}</span>
              <div className="text-[10px] text-[var(--muted)]">
                <span className="mr-3">{g.member_count} members</span>
                <span>Reviewed: {g.last_reviewed?.slice(0, 10)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Simulated note */}
      {data.note && (
        <p className="text-[10px] text-[var(--muted)]/60 italic mt-2">{String(data.note)}</p>
      )}
    </div>
  );
}
