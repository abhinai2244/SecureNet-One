"use client";

import { useEffect, useState } from "react";
import { getDeviceStats, getLogStats } from "@/lib/api";
import type { DeviceStats, LogStats } from "@/types";

export default function DashboardPage() {
  const [deviceStats, setDeviceStats] = useState<DeviceStats | null>(null);
  const [logStats, setLogStats] = useState<LogStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [ds, ls] = await Promise.allSettled([
          getDeviceStats(),
          getLogStats(),
        ]);
        if (ds.status === "fulfilled") setDeviceStats(ds.value);
        if (ls.status === "fulfilled") setLogStats(ls.value);
      } catch {
        // Stats may fail if no data yet
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const stats = [
    {
      label: "Total Devices",
      value: deviceStats?.total_devices ?? 0,
      icon: "💻",
      color: "var(--primary-500)",
      bg: "rgba(99, 102, 241, 0.12)",
    },
    {
      label: "Online",
      value: deviceStats?.online_devices ?? 0,
      icon: "🟢",
      color: "var(--accent-500)",
      bg: "rgba(16, 185, 129, 0.12)",
    },
    {
      label: "Offline",
      value: deviceStats?.offline_devices ?? 0,
      icon: "🔴",
      color: "var(--danger-500)",
      bg: "rgba(244, 63, 94, 0.12)",
    },
    {
      label: "DNS Queries",
      value: logStats?.total_dns_queries ?? 0,
      icon: "🌐",
      color: "var(--warning-500)",
      bg: "rgba(245, 158, 11, 0.12)",
    },
    {
      label: "Avg Latency",
      value: logStats?.average_latency_ms ? `${logStats.average_latency_ms}ms` : "—",
      icon: "⚡",
      color: "var(--primary-500)",
      bg: "rgba(99, 102, 241, 0.12)",
    },
  ];

  const securityStats = [
    {
      label: "Encrypted Devices",
      value: deviceStats?.encrypted_devices ?? 0,
      total: deviceStats?.total_devices ?? 0,
      icon: "🔐",
    },
    {
      label: "Antivirus Active",
      value: deviceStats?.antivirus_active_devices ?? 0,
      total: deviceStats?.total_devices ?? 0,
      icon: "🛡️",
    },
    {
      label: "Blocked Queries",
      value: logStats?.blocked_queries ?? 0,
      total: logStats?.total_dns_queries ?? 1,
      icon: "🚫",
    },
    {
      label: "Connection Errors",
      value: logStats?.total_errors ?? 0,
      total: logStats?.total_connections ?? 1,
      icon: "⚠️",
    },
  ];

  return (
    <div>
      {/* Stats Cards */}
      <div className="grid grid-cols-5 mb-lg">
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            className="glass-card stats-card animate-fade-in"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div
              className="stats-icon"
              style={{ background: stat.bg, color: stat.color }}
            >
              {stat.icon}
            </div>
            <div className="stats-value" style={{ color: stat.color }}>
              {loading ? "—" : stat.value.toLocaleString()}
            </div>
            <div className="stats-label">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Security & Threat Overview */}
      <div className="grid grid-cols-3 mb-lg gap-lg">
        {/* Security Posture */}
        <div className="glass-card animate-fade-in" style={{ padding: "var(--space-xl)" }}>
          <h3 className="mb-lg">🛡️ Security Posture</h3>
          <div className="flex flex-col gap-lg">
            {securityStats.map((item) => {
              const pct = item.total > 0 ? Math.round((item.value / item.total) * 100) : 0;
              return (
                <div key={item.label}>
                  <div className="flex justify-between items-center mb-sm">
                    <span className="text-sm">
                      {item.icon} {item.label}
                    </span>
                    <span className="text-sm font-mono">
                      {item.value}/{item.total} ({pct}%)
                    </span>
                  </div>
                  <div
                    style={{
                      height: "6px",
                      background: "var(--bg-tertiary)",
                      borderRadius: "var(--radius-full)",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${pct}%`,
                        background: pct > 80 ? "var(--accent-500)" : pct > 50 ? "var(--warning-500)" : "var(--danger-500)",
                        borderRadius: "var(--radius-full)",
                        transition: "width 1s ease-out",
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Blocked Domains */}
        <div className="glass-card animate-fade-in" style={{ padding: "var(--space-xl)", animationDelay: "200ms" }}>
          <h3 className="mb-lg">🚫 Top Blocked Domains</h3>
          {logStats?.top_blocked_domains && logStats.top_blocked_domains.length > 0 ? (
            <div className="flex flex-col gap-md">
              {logStats.top_blocked_domains.slice(0, 8).map((item, i) => (
                <div
                  key={item.domain}
                  className="flex justify-between items-center"
                  style={{
                    padding: "0.5rem 0.75rem",
                    background: "rgba(244, 63, 94, 0.05)",
                    borderRadius: "var(--radius-md)",
                    borderLeft: "3px solid var(--danger-400)",
                  }}
                >
                  <span className="text-sm font-mono truncate" style={{ maxWidth: "70%" }}>
                    {item.domain}
                  </span>
                  <span className="badge badge-danger">{item.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">🎉</div>
              <p>No blocked domains yet</p>
              <p className="text-xs text-muted mt-md">
                Create a DNS policy to start filtering
              </p>
            </div>
          )}
        </div>

        {/* Top Requested Domains */}
        <div className="glass-card animate-fade-in" style={{ padding: "var(--space-xl)", animationDelay: "250ms" }}>
          <h3 className="mb-lg">📊 Top Requested Domains</h3>
          {logStats?.top_requested_domains && logStats.top_requested_domains.length > 0 ? (
            <div className="flex flex-col gap-md">
              {logStats.top_requested_domains.slice(0, 8).map((item, i) => (
                <div
                  key={item.domain}
                  className="flex justify-between items-center"
                  style={{
                    padding: "0.5rem 0.75rem",
                    background: "rgba(99, 102, 241, 0.05)",
                    borderRadius: "var(--radius-md)",
                    borderLeft: "3px solid var(--primary-400)",
                  }}
                >
                  <span className="text-sm font-mono truncate" style={{ maxWidth: "70%" }}>
                    {item.domain}
                  </span>
                  <span className="badge badge-primary">{item.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">🌐</div>
              <p>No domains requested yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Events */}
      <div className="glass-card animate-fade-in" style={{ padding: "var(--space-xl)", animationDelay: "300ms" }}>
        <h3 className="mb-lg">📋 Recent Events</h3>
        {logStats?.recent_events && logStats.recent_events.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Device</th>
                  <th>Event</th>
                  <th>Source IP</th>
                </tr>
              </thead>
              <tbody>
                {logStats.recent_events.slice(0, 10).map((event) => (
                  <tr key={event.id}>
                    <td className="font-mono text-xs">
                      {new Date(event.timestamp).toLocaleString()}
                    </td>
                    <td className="text-sm truncate">{event.device_id?.slice(0, 8)}...</td>
                    <td>
                      <span
                        className={`badge ${
                          event.event_type === "connect"
                            ? "badge-online"
                            : event.event_type === "error"
                            ? "badge-danger"
                            : "badge-primary"
                        }`}
                      >
                        {event.event_type}
                      </span>
                    </td>
                    <td className="font-mono text-sm">{event.source_ip || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">📡</div>
            <p>No events recorded yet</p>
            <p className="text-xs text-muted mt-md">
              Connect a device to start seeing events
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
