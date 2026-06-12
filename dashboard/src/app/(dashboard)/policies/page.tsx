"use client";

import { useEffect, useState } from "react";
import { getPolicies, createPolicy, deletePolicy, updatePolicy } from "@/lib/api";
import type { Policy, PolicyListResponse } from "@/types";

const policyTypes = ["dns", "tunnel", "access", "posture"] as const;
const typeIcons: Record<string, string> = {
  dns: "🌐",
  tunnel: "🔗",
  access: "🚪",
  posture: "📋",
};

export default function PoliciesPage() {
  const [data, setData] = useState<PolicyListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>("all");
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    type: "dns",
    enabled: true,
    priority: 100,
    rules: '{\n  "blocked_domains": ["example-malware.com", "*.tracking.net"],\n  "blocked_categories": ["malware", "phishing"]\n}',
  });

  useEffect(() => {
    fetchPolicies();
  }, [activeTab]);

  async function fetchPolicies() {
    setLoading(true);
    try {
      const typeFilter = activeTab === "all" ? undefined : activeTab;
      const result = await getPolicies(1, 50, typeFilter);
      setData(result);
    } catch {
      // handle error
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    try {
      let parsedRules = {};
      try {
        parsedRules = JSON.parse(formData.rules);
      } catch {
        alert("Invalid JSON in rules field");
        return;
      }

      await createPolicy({
        name: formData.name,
        description: formData.description,
        type: formData.type as Policy["type"],
        enabled: formData.enabled,
        priority: formData.priority,
        rules: parsedRules,
      });

      setShowModal(false);
      setFormData({
        name: "",
        description: "",
        type: "dns",
        enabled: true,
        priority: 100,
        rules: '{\n  "blocked_domains": [],\n  "blocked_categories": []\n}',
      });
      fetchPolicies();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create policy");
    }
  }

  async function handleToggle(policy: Policy) {
    try {
      await updatePolicy(policy.id, { enabled: !policy.enabled });
      fetchPolicies();
    } catch {
      // handle error
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this policy?")) return;
    try {
      await deletePolicy(id);
      fetchPolicies();
    } catch {
      // handle error
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-lg">
        <div>
          <h2>Policy Management</h2>
          <p className="text-sm text-muted mt-sm">
            {data?.total ?? 0} policies configured
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowModal(true)}
          id="create-policy-btn"
        >
          ➕ Create Policy
        </button>
      </div>

      {/* Type Tabs */}
      <div className="tabs">
        {["all", ...policyTypes].map((type) => (
          <button
            key={type}
            className={`tab ${activeTab === type ? "active" : ""}`}
            onClick={() => setActiveTab(type)}
          >
            {type !== "all" && typeIcons[type]} {type.charAt(0).toUpperCase() + type.slice(1)}
          </button>
        ))}
      </div>

      {/* Policy Cards */}
      <div className="grid grid-cols-2">
        {loading ? (
          <div className="glass-card" style={{ padding: "3rem", gridColumn: "1 / -1" }}>
            <div className="text-center text-muted">Loading policies...</div>
          </div>
        ) : data?.policies && data.policies.length > 0 ? (
          data.policies.map((policy, i) => (
            <div
              key={policy.id}
              className="glass-card animate-fade-in"
              style={{
                padding: "var(--space-lg)",
                animationDelay: `${i * 80}ms`,
                opacity: policy.enabled ? 1 : 0.6,
              }}
            >
              <div className="flex justify-between items-center mb-md">
                <div className="flex items-center gap-md">
                  <span style={{ fontSize: "1.5rem" }}>
                    {typeIcons[policy.type] || "📄"}
                  </span>
                  <div>
                    <div style={{ fontWeight: 600 }}>{policy.name}</div>
                    <div className="text-xs text-muted">{policy.description || "No description"}</div>
                  </div>
                </div>
                <span className={`badge ${policy.type === "dns" ? "badge-primary" : policy.type === "tunnel" ? "badge-online" : policy.type === "access" ? "badge-warning" : "badge-danger"}`}>
                  {policy.type}
                </span>
              </div>

              {/* Rules preview */}
              <div
                className="font-mono text-xs"
                style={{
                  padding: "0.75rem",
                  background: "var(--bg-primary)",
                  borderRadius: "var(--radius-md)",
                  maxHeight: "80px",
                  overflow: "hidden",
                  color: "var(--text-secondary)",
                  marginBottom: "var(--space-md)",
                }}
              >
                {JSON.stringify(policy.rules, null, 2).slice(0, 150)}...
              </div>

              <div className="flex justify-between items-center">
                <div className="flex items-center gap-md">
                  <span className="text-xs text-muted">Priority: {policy.priority}</span>
                  <button
                    className={`btn btn-sm ${policy.enabled ? "btn-secondary" : "btn-primary"}`}
                    onClick={() => handleToggle(policy)}
                  >
                    {policy.enabled ? "Disable" : "Enable"}
                  </button>
                </div>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => handleDelete(policy.id)}
                  title="Delete"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="glass-card" style={{ padding: "3rem", gridColumn: "1 / -1" }}>
            <div className="empty-state">
              <div className="empty-icon">🔒</div>
              <p>No policies configured</p>
              <p className="text-xs text-muted mt-md">
                Create your first policy to enforce security rules
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Create Policy Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create New Policy</h3>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowModal(false)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="flex flex-col gap-lg">
                <div className="input-group">
                  <label>Policy Name</label>
                  <input
                    className="input"
                    placeholder="Block malware domains"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    id="policy-name-input"
                  />
                </div>
                <div className="input-group">
                  <label>Description</label>
                  <input
                    className="input"
                    placeholder="Optional description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
                <div className="input-group">
                  <label>Type</label>
                  <select
                    className="input"
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    id="policy-type-select"
                  >
                    {policyTypes.map((t) => (
                      <option key={t} value={t}>
                        {typeIcons[t]} {t.charAt(0).toUpperCase() + t.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="input-group">
                  <label>Priority (1-1000, lower = higher priority)</label>
                  <input
                    className="input"
                    type="number"
                    min={1}
                    max={1000}
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 100 })}
                  />
                </div>
                <div className="input-group">
                  <label>Rules (JSON)</label>
                  <textarea
                    className="input font-mono"
                    rows={6}
                    value={formData.rules}
                    onChange={(e) => setFormData({ ...formData, rules: e.target.value })}
                    style={{ resize: "vertical" }}
                    id="policy-rules-input"
                  />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleCreate} id="policy-submit-btn">
                Create Policy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
