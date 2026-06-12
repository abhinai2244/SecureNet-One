"use client";

import { useEffect, useState } from "react";
import { getUsers } from "@/lib/api";
import type { User, UserListResponse } from "@/types";

const roleBadge: Record<string, string> = {
  super_admin: "badge-danger",
  admin: "badge-warning",
  analyst: "badge-primary",
  user: "badge-online",
};

const roleLabels: Record<string, string> = {
  super_admin: "Super Admin",
  admin: "Admin",
  analyst: "Analyst",
  user: "User",
};

export default function UsersPage() {
  const [data, setData] = useState<UserListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchUsers();
  }, [page]);

  async function fetchUsers() {
    setLoading(true);
    try {
      const result = await getUsers(page);
      setData(result);
    } catch {
      // handle error
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-lg">
        <div>
          <h2>User Management</h2>
          <p className="text-sm text-muted mt-sm">
            {data?.total ?? 0} registered users
          </p>
        </div>
        <button className="btn btn-secondary" onClick={fetchUsers}>
          🔄 Refresh
        </button>
      </div>

      {/* Users Table */}
      <div className="glass-card animate-fade-in">
        <div className="table-container">
          <table className="table" id="users-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={4} className="text-center text-muted" style={{ padding: "3rem" }}>
                    Loading users...
                  </td>
                </tr>
              ) : data?.users && data.users.length > 0 ? (
                data.users.map((user: User, i: number) => (
                  <tr key={user.id} className="animate-fade-in" style={{ animationDelay: `${i * 50}ms` }}>
                    <td>
                      <div className="flex items-center gap-md">
                        <div className="avatar" style={{ width: 32, height: 32, fontSize: "0.7rem" }}>
                          {user.full_name?.charAt(0)?.toUpperCase() || "U"}
                        </div>
                        <div>
                          <div style={{ fontWeight: 500 }}>{user.full_name}</div>
                          <div className="text-xs text-muted">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${roleBadge[user.role] || "badge-primary"}`}>
                        {roleLabels[user.role] || user.role}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${user.is_active ? "badge-online" : "badge-offline"}`}>
                        {user.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="text-sm text-muted">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4}>
                    <div className="empty-state">
                      <div className="empty-icon">👥</div>
                      <p>No users found</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {data && data.total > 20 && (
          <div className="flex justify-between items-center" style={{ padding: "var(--space-md) var(--space-lg)", borderTop: "1px solid var(--border-default)" }}>
            <span className="text-sm text-muted">Page {page} of {Math.ceil(data.total / 20)}</span>
            <div className="flex gap-sm">
              <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Previous</button>
              <button className="btn btn-secondary btn-sm" disabled={page >= Math.ceil(data.total / 20)} onClick={() => setPage(page + 1)}>Next →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
