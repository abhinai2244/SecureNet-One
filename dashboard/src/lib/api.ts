// ═══════════════════════════════════════════════════════════════════
// SecureNet One — API Client
// Typed fetch wrapper with JWT token management
// ═══════════════════════════════════════════════════════════════════

import type {
  LoginResponse,
  DeviceListResponse,
  DeviceStats,
  PolicyListResponse,
  Policy,
  LogStats,
  UserListResponse,
  User,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// ── Token Management ────────────────────────────────────────────────
function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  const data = localStorage.getItem('user');
  return data ? JSON.parse(data) : null;
}

function setUser(user: User) {
  localStorage.setItem('user', JSON.stringify(user));
}

// ── Fetch Wrapper ───────────────────────────────────────────────────
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearTokens();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// ── Auth API ────────────────────────────────────────────────────────
export async function login(email: string, password: string): Promise<LoginResponse> {
  const data = await apiFetch<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setTokens(data.tokens.access_token, data.tokens.refresh_token);
  setUser(data.user);
  return data;
}

export async function register(email: string, password: string, fullName: string): Promise<LoginResponse> {
  const data = await apiFetch<LoginResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  setTokens(data.tokens.access_token, data.tokens.refresh_token);
  setUser(data.user);
  return data;
}

export function logout() {
  clearTokens();
  window.location.href = '/login';
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function getCurrentUser(): User | null {
  return getUser();
}

// ── Devices API ─────────────────────────────────────────────────────
export async function getDevices(page = 1, pageSize = 20): Promise<DeviceListResponse> {
  return apiFetch(`/devices?page=${page}&page_size=${pageSize}`);
}

export async function getDeviceStats(): Promise<DeviceStats> {
  return apiFetch('/devices/stats');
}

export async function deleteDevice(deviceId: string): Promise<void> {
  await apiFetch(`/devices/${deviceId}`, { method: 'DELETE' });
}

// ── Policies API ────────────────────────────────────────────────────
export async function getPolicies(page = 1, pageSize = 20, type?: string): Promise<PolicyListResponse> {
  let url = `/policies?page=${page}&page_size=${pageSize}`;
  if (type) url += `&type=${type}`;
  return apiFetch(url);
}

export async function createPolicy(data: Partial<Policy>): Promise<Policy> {
  return apiFetch('/policies', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updatePolicy(id: string, data: Partial<Policy>): Promise<Policy> {
  return apiFetch(`/policies/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deletePolicy(id: string): Promise<void> {
  await apiFetch(`/policies/${id}`, { method: 'DELETE' });
}

// ── Logs API ────────────────────────────────────────────────────────
export async function getLogStats(): Promise<LogStats> {
  return apiFetch('/logs/stats');
}

export async function getDeviceLogs(page = 1, pageSize = 50, deviceId?: string) {
  let url = `/logs/devices?page=${page}&page_size=${pageSize}`;
  if (deviceId) url += `&device_id=${deviceId}`;
  return apiFetch(url);
}

export async function getDnsLogs(page = 1, pageSize = 50, action?: string) {
  let url = `/logs/dns?page=${page}&page_size=${pageSize}`;
  if (action) url += `&action=${action}`;
  return apiFetch(url);
}

// ── Users API ───────────────────────────────────────────────────────
export async function getUsers(page = 1, pageSize = 20): Promise<UserListResponse> {
  return apiFetch(`/auth/users?page=${page}&page_size=${pageSize}`);
}
