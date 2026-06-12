# SecureNet One — Architecture Documentation

## System Overview

SecureNet One is a Zero Trust security platform inspired by Cloudflare One / WARP. It enforces "never trust, always verify" by requiring all devices to authenticate, establish encrypted tunnels, and pass security posture checks before accessing network resources.

## Component Architecture

```
                    ┌──────────────────────────────┐
                    │        Internet               │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │     Nginx Reverse Proxy       │
                    │     (TLS Termination)         │
                    │     Port 8080                 │
                    └──────┬───────────┬───────────┘
                           │           │
              ┌────────────▼───┐  ┌────▼──────────┐
              │  FastAPI       │  │  Next.js       │
              │  Backend       │  │  Dashboard     │
              │  Port 8000     │  │  Port 3000     │
              │                │  │                │
              │  Modules:      │  │  Pages:        │
              │  • Auth        │  │  • Login       │
              │  • Devices     │  │  • Dashboard   │
              │  • Policies    │  │  • Devices     │
              │  • Logs        │  │  • Policies    │
              │  • WireGuard   │  │  • Logs        │
              │  • DNS/DoH     │  │  • Users       │
              └──┬─────────┬───┘  └────────────────┘
                 │         │
          ┌──────▼──┐  ┌───▼──────┐
          │PostgreSQL│  │  Redis   │
          │  :5432   │  │  :6379   │
          │          │  │          │
          │ Tables:  │  │ Stores:  │
          │ • users  │  │ • tokens │
          │ • devices│  │ • cache  │
          │ • polici…│  │ • status │
          │ • logs   │  │          │
          │ • wg_peer│  │          │
          └──────────┘  └──────────┘
```

## Data Flow

### 1. Device Registration Flow
```
Agent → POST /api/auth/login → JWT Token
Agent → POST /api/devices/register (+ posture data) → Device ID + Assigned IP
Agent → GET /api/wireguard/config/{device_id} → WireGuard Config
Agent → Creates WireGuard Tunnel via Wintun
Agent → Starts DNS interception → DoH endpoint
Agent → Periodic POST /api/devices/heartbeat
```

### 2. DNS Resolution Flow
```
Application → DNS Query → Agent DNS Interceptor
Agent → POST /api/dns/dns-query (wire format) → Backend DoH
Backend → Check DNS Policies (blocked_domains, categories)
  → If blocked: Return NXDOMAIN + log
  → If allowed: Forward to upstream (1.1.1.1) + log
Backend → Return DNS response → Agent → Application
```

### 3. Policy Enforcement Flow
```
Admin → Dashboard → Create Policy (type: dns/tunnel/access/posture)
Policy stored in PostgreSQL
Agent heartbeat → Backend checks posture against policies
DNS query → Backend evaluates domain against DNS policies
Tunnel config → Backend applies tunnel policies (full/split)
```

## Security Model

| Layer | Implementation |
|-------|---------------|
| Authentication | JWT (HS256) with 15min access + 7d refresh tokens |
| Authorization | RBAC: super_admin > admin > analyst > user |
| Transport | WireGuard (ChaCha20-Poly1305) for tunnel, HTTPS for API |
| DNS Privacy | All DNS via HTTPS (RFC 8484) |
| Data at Rest | PostgreSQL with hashed passwords (bcrypt), encrypted WG keys |
| Session Mgmt | Redis-backed token blacklist |
| Audit | All admin actions logged with user, IP, timestamp |

## Technology Stack

| Component | Technology | Reason |
|-----------|-----------|--------|
| Backend API | FastAPI (Python) | Async, auto-docs, Pydantic validation |
| Database | PostgreSQL 16 | JSONB for flexible rules, UUID support |
| Cache | Redis 7 | Token blacklisting, device status TTL |
| Dashboard | Next.js 14 (TypeScript) | SSR, App Router, modern React |
| Agent | Go | Cross-platform, WireGuard libraries, performance |
| Tunnel | WireGuard + Wintun | Modern VPN, kernel-level performance |
| DNS | dnspython + httpx | RFC 8484 DoH, policy-based filtering |
| Deployment | Docker Compose + Nginx | Container orchestration, reverse proxy |
