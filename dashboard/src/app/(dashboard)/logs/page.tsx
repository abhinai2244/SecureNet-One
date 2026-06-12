"use client";

import { useEffect, useState } from "react";
import { getDnsLogs, getDeviceLogs } from "@/lib/api";
import type { DnsLog, DeviceLog } from "@/types";

type LogTab = "dns" | "device";

export default function LogsPage() {
  const [activeTab, setActiveTab] = useState<LogTab>("dns");
  const [dnsLogs, setDnsLogs] = useState<DnsLog[]>([]);
  const [deviceLogs, setDeviceLogs] = useState<DeviceLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [dnsFilter, setDnsFilter] = useState<string>("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchLogs();
  }, [activeTab, dnsFilter, page]);

  async function fetchLogs() {
    setLoading(true);
    try {
      if (activeTab === "dns") {
        const result = await getDnsLogs(page, 50, dnsFilter || undefined) as { logs: DnsLog[]; total: number };
        setDnsLogs(result.logs || []);
        setTotal(result.total || 0);
      } else {
        const result = await getDeviceLogs(page, 50) as { logs: DeviceLog[]; total: number };
        setDeviceLogs(result.logs || []);
        setTotal(result.total || 0);
      }
    } catch {
      // handle error
    } finally {
      setLoading(false);
    }
  }

  function getActionBadge(action: string) {
    switch (action) {
      case "allow": return "badge-online";
      case "block": return "badge-danger";
      case "redirect": return "badge-warning";
      default: return "badge-primary";
    }
  }

  function getEventBadge(type: string) {
    switch (type) {
      case "connect": return "badge-online";
      case "disconnect": return "badge-offline";
      case "error": return "badge-danger";
      case "heartbeat": return "badge-primary";
      default: return "badge-warning";
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-lg">
        <div>
          <h2>System Logs</h2>
          <p className="text-sm text-muted mt-sm">{total} log entries</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchLogs} id="refresh-logs">
          🔄 Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === "dns" ? "active" : ""}`}
          onClick={() => { setActiveTab("dns"); setPage(1); }}
        >
          🌐 DNS Queries
        </button>
        <button
          className={`tab ${activeTab === "device" ? "active" : ""}`}
          onClick={() => { setActiveTab("device"); setPage(1); }}
        >
          💻 Device Events
        </button>
      </div>

      {/* DNS Filters */}
      {activeTab === "dns" && (
        <div className="flex gap-md mb-lg animate-fade-in">
          {["", "allow", "block"].map((filter) => (
            <button
              key={filter}
              className={`btn btn-sm ${dnsFilter === filter ? "btn-primary" : "btn-secondary"}`}
              onClick={() => { setDnsFilter(filter); setPage(1); }}
            >
              {filter === "" ? "All" : filter === "allow" ? "✅ Allowed" : "🚫 Blocked"}
            </button>
          ))}
        </div>
      )}

      {/* Log Table */}
      <div className="glass-card animate-fade-in">
        <div className="table-container" style={{ maxHeight: "65vh", overflowY: "auto" }}>
          {activeTab === "dns" ? (
            <table className="table" id="dns-logs-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Domain</th>
                  <th>Type</th>
                  <th>Action</th>
                  <th>Response</th>
                  <th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={6} className="text-center text-muted" style={{ padding: "3rem" }}>Loading...</td></tr>
                ) : dnsLogs.length > 0 ? (
                  dnsLogs.map((log) => (
                    <tr key={log.id}>
                      <td className="font-mono text-xs">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </td>
                      <td>
                        <span className="font-mono text-sm truncate" style={{ maxWidth: "300px", display: "inline-block" }}>
                          {log.query_name}
                        </span>
                      </td>
                      <td className="badge badge-primary" style={{ fontSize: "0.7rem" }}>
                        {log.query_type}
                      </td>
                      <td>
                        <span className={`badge ${getActionBadge(log.action)}`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="text-sm text-muted">{log.response_code || "—"}</td>
                      <td className="font-mono text-sm">
                        {log.response_time_ms != null ? `${log.response_time_ms}ms` : "—"}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6}>
                      <div className="empty-state">
                        <div className="empty-icon">🌐</div>
                        <p>No DNS logs recorded</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          ) : (
            <table className="table" id="device-logs-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Device ID</th>
                  <th>Event</th>
                  <th>Source IP</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={5} className="text-center text-muted" style={{ padding: "3rem" }}>Loading...</td></tr>
                ) : deviceLogs.length > 0 ? (
                  deviceLogs.map((log) => (
                    <tr key={log.id}>
                      <td className="font-mono text-xs">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="font-mono text-sm">{log.device_id?.slice(0, 12)}...</td>
                      <td>
                        <span className={`badge ${getEventBadge(log.event_type)}`}>
                          {log.event_type}
                        </span>
                      </td>
                      <td className="font-mono text-sm">{log.source_ip || "—"}</td>
                      <td className="text-xs text-muted truncate" style={{ maxWidth: "200px" }}>
                        {log.payload ? JSON.stringify(log.payload).slice(0, 60) : "—"}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5}>
                      <div className="empty-state">
                        <div className="empty-icon">📋</div>
                        <p>No device logs recorded</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {total > 50 && (
          <div className="flex justify-between items-center" style={{ padding: "var(--space-md) var(--space-lg)", borderTop: "1px solid var(--border-default)" }}>
            <span className="text-sm text-muted">Page {page} of {Math.ceil(total / 50)}</span>
            <div className="flex gap-sm">
              <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Prev</button>
              <button className="btn btn-secondary btn-sm" disabled={page >= Math.ceil(total / 50)} onClick={() => setPage(page + 1)}>Next →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
