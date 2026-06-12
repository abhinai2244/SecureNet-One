// ═══════════════════════════════════════════════════════════════════
// SecureNet One — TypeScript Type Definitions
// ═══════════════════════════════════════════════════════════════════

// ── Auth ────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'super_admin' | 'admin' | 'analyst' | 'user';
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  user: User;
  tokens: TokenResponse;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  page_size: number;
}

// ── Devices ─────────────────────────────────────────────────────────
export interface Device {
  id: string;
  user_id: string;
  device_name: string;
  hostname: string;
  os: string;
  os_version: string | null;
  agent_version: string | null;
  status: 'online' | 'offline' | 'warning';
  public_key: string | null;
  assigned_ip: string | null;
  last_ip: string | null;
  last_seen: string | null;
  disk_encrypted: boolean | null;
  antivirus_active: boolean | null;
  cpu_info: string | null;
  ram_bytes: number | null;
  created_at: string;
}

export interface DeviceListResponse {
  devices: Device[];
  total: number;
  page: number;
  page_size: number;
}

export interface DeviceStats {
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  warning_devices: number;
  encrypted_devices: number;
  antivirus_active_devices: number;
}

// ── Policies ────────────────────────────────────────────────────────
export interface Policy {
  id: string;
  name: string;
  description: string | null;
  type: 'dns' | 'tunnel' | 'access' | 'posture';
  rules: Record<string, unknown>;
  enabled: boolean;
  priority: number;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface PolicyListResponse {
  policies: Policy[];
  total: number;
  page: number;
  page_size: number;
}

// ── Logs ────────────────────────────────────────────────────────────
export interface DeviceLog {
  id: string;
  device_id: string;
  event_type: string;
  payload: Record<string, unknown> | null;
  source_ip: string | null;
  timestamp: string;
}

export interface DnsLog {
  id: string;
  device_id: string | null;
  query_name: string;
  query_type: string;
  response_code: string | null;
  action: 'allow' | 'block' | 'redirect';
  policy_id: string | null;
  response_time_ms: number | null;
  timestamp: string;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  changes: Record<string, unknown> | null;
  source_ip: string | null;
  timestamp: string;
}

export interface LogStats {
  total_dns_queries: number;
  blocked_queries: number;
  total_connections: number;
  total_errors: number;
  top_blocked_domains: { domain: string; count: number }[];
  recent_events: DeviceLog[];
}

// ── WireGuard ───────────────────────────────────────────────────────
export interface WireGuardStatus {
  server_public_key: string;
  server_endpoint: string;
  total_peers: number;
  active_peers: number;
}
