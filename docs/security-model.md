# SecureNet One — Security Model

## Authentication

### JWT Token Flow
```
User → POST /api/auth/login (email, password)
  → Server validates credentials (bcrypt hash comparison)
  → Server generates:
     • Access Token (15 min TTL, contains: user_id, role, type=access)
     • Refresh Token (7 day TTL, contains: user_id, type=refresh)
  → Client stores tokens in localStorage
  → All API requests include: Authorization: Bearer <access_token>
  → On 401: Client uses refresh token → POST /api/auth/refresh
  → On logout: Token added to Redis blacklist
```

### Password Security
- **Hashing**: bcrypt with automatic salt generation
- **Minimum Length**: 8 characters enforced by Pydantic validation
- **Storage**: Only bcrypt hash stored, never plaintext

## Authorization (RBAC)

| Role | Permissions |
|------|-----------|
| **Super Admin** | Full system access, user role management, audit logs |
| **Admin** | Device management, policy CRUD, log viewing |
| **Analyst** | Read-only access to devices, logs, and statistics |
| **User** | Own device management, profile access only |

## Transport Security

### WireGuard Tunnel
- **Protocol**: WireGuard (UDP)
- **Encryption**: ChaCha20-Poly1305
- **Key Exchange**: Curve25519 (X25519)
- **Key Size**: 256-bit
- **MTU**: 1420 (accounting for encapsulation overhead)
- **Keepalive**: 25 seconds

### DNS-over-HTTPS (DoH)
- **Standard**: RFC 8484
- **Transport**: HTTPS (TLS 1.3)
- **Upstream**: Configurable (default: Cloudflare 1.1.1.1)
- **Filtering**: Policy-based domain blocking before forwarding

## Device Trust

### Posture Checks
The agent periodically reports:
- OS version and patch level
- Disk encryption status (BitLocker on Windows)
- Antivirus presence and status
- Running security software
- Hardware info (CPU, RAM)

### Heartbeat
- **Interval**: 60 seconds (configurable)
- **Offline Threshold**: 180 seconds
- **Status**: Tracked via Redis TTL keys for real-time status

## Audit Trail
All administrative actions are logged:
- User ID performing the action
- Action type (create, update, delete)
- Resource type and ID
- JSON diff of changes
- Source IP address
- Timestamp

## Key Management
- **Server Keys**: Stored in environment variables
- **Device Keys**: Generated server-side via X25519
- **Key Rotation**: Supported via `/api/wireguard/rotate-keys/{device_id}`
- **Preshared Keys**: Additional layer of post-quantum resistance
