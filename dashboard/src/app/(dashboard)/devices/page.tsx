"use client";

import { useEffect, useState } from "react";
import { getDevices, deleteDevice } from "@/lib/api";
import type { Device, DeviceListResponse } from "@/types";

export default function DevicesPage() {
  const [data, setData] = useState<DeviceListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchDevices();
  }, [page]);

  async function fetchDevices() {
    setLoading(true);
    try {
      const result = await getDevices(page);
      setData(result);
    } catch {
      // handle error
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Are you sure you want to remove this device?")) return;
    try {
      await deleteDevice(id);
      fetchDevices();
    } catch {
      // handle error
    }
  }

  function getStatusBadge(status: string) {
    const map: Record<string, string> = {
      online: "badge-online",
      offline: "badge-offline",
      warning: "badge-warning",
    };
    return map[status] || "badge-offline";
  }

  function formatBytes(bytes: number | null) {
    if (!bytes) return "—";
    const gb = bytes / (1024 * 1024 * 1024);
    return `${gb.toFixed(1)} GB`;
  }

  function timeAgo(dateStr: string | null) {
    if (!dateStr) return "Never";
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-lg">
        <div>
          <h2>Device Inventory</h2>
          <p className="text-sm text-muted mt-sm">
            {data?.total ?? 0} devices registered
          </p>
        </div>
        <button className="btn btn-primary" id="refresh-devices" onClick={fetchDevices}>
          🔄 Refresh
        </button>
      </div>

      {/* Device Table */}
      <div className="glass-card animate-fade-in">
        <div className="table-container">
          <table className="table" id="devices-table">
            <thead>
              <tr>
                <th>Device</th>
                <th>Status</th>
                <th>OS</th>
                <th>IP Address</th>
                <th>Last Seen</th>
                <th>Security</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center text-muted" style={{ padding: "3rem" }}>
                    Loading devices...
                  </td>
                </tr>
              ) : data?.devices && data.devices.length > 0 ? (
                data.devices.map((device: Device) => (
                  <tr key={device.id}>
                    <td>
                      <div>
                        <div style={{ fontWeight: 500 }}>{device.device_name}</div>
                        <div className="text-xs text-muted font-mono">
                          {device.hostname}
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${getStatusBadge(device.status)}`}>
                        {device.status}
                      </span>
                    </td>
                    <td>
                      <div className="text-sm">{device.os}</div>
                      <div className="text-xs text-muted">{device.os_version || "—"}</div>
                    </td>
                    <td className="font-mono text-sm">{device.assigned_ip || "—"}</td>
                    <td className="text-sm">{timeAgo(device.last_seen)}</td>
                    <td>
                      <div className="flex gap-sm">
                        <span title="Disk Encryption" style={{ opacity: device.disk_encrypted ? 1 : 0.3 }}>
                          🔐
                        </span>
                        <span title="Antivirus" style={{ opacity: device.antivirus_active ? 1 : 0.3 }}>
                          🛡️
                        </span>
                      </div>
                    </td>
                    <td>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => handleDelete(device.id)}
                        title="Remove device"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7}>
                    <div className="empty-state">
                      <div className="empty-icon">💻</div>
                      <p>No devices registered</p>
                      <p className="text-xs text-muted mt-md">
                        Install the SecureNet One agent on a device to get started
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total > 20 && (
          <div
            className="flex justify-between items-center"
            style={{
              padding: "var(--space-md) var(--space-lg)",
              borderTop: "1px solid var(--border-default)",
            }}
          >
            <span className="text-sm text-muted">
              Page {page} of {Math.ceil(data.total / 20)}
            </span>
            <div className="flex gap-sm">
              <button
                className="btn btn-secondary btn-sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                ← Previous
              </button>
              <button
                className="btn btn-secondary btn-sm"
                disabled={page >= Math.ceil(data.total / 20)}
                onClick={() => setPage(page + 1)}
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
