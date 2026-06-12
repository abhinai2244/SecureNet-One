# 🛡️ SecureNet One

> A production-style MVP of a **Cloudflare One / WARP-inspired Zero Trust Security Platform**, built as a final-year cybersecurity project.

---

## 🏗️ Architecture

```
┌─────────────────────┐
│   Desktop Agent     │  Go (Windows)
│   (System Tray)     │  WireGuard + DoH
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   WireGuard Tunnel  │  Encrypted UDP
│   + DoH DNS         │  HTTPS DNS
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Gateway Server    │
│   ┌───────┬───────┐ │
│   │FastAPI│ DoH   │ │
│   │Backend│Server │ │
│   └───┬───┴───┬───┘ │
│       │       │     │
│   ┌───┴───┬───┴───┐ │
│   │Postgre│ Redis │ │
│   │  SQL  │       │ │
│   └───────┴───────┘ │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│   Next.js Dashboard │  React + TypeScript
│   (Management UI)   │
└─────────────────────┘
```

## 📦 Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI + PostgreSQL + Redis | REST API, auth, device management, WireGuard config |
| **Dashboard** | Next.js 14 + TypeScript | Admin panel with device, policy, and log management |
| **Agent** | Go + Wintun | Windows desktop agent with tunnel and DoH |
| **Deployment** | Docker Compose + Nginx | Container orchestration and reverse proxy |

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Go 1.21+
- Docker Desktop

### 1. Start Infrastructure (PostgreSQL + Redis)
```bash
cd deployment
docker compose up postgres redis -d
```

### 2. Start Backend
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Start Dashboard
```bash
cd dashboard
npm install
npm run dev
```

### 4. Build Agent (optional)
```bash
cd agent
go build -o securenet.exe ./cmd/securenet/
./securenet.exe --server http://localhost:8000/api --email admin@test.com --password password123
```

### 5. Full Docker Deployment
```bash
cd deployment
docker compose up --build
```

Access: `http://localhost:8080` (Nginx) or `http://localhost:3000` (Dashboard direct)

## 📡 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register user |
| `POST` | `/api/auth/login` | Login |
| `POST` | `/api/devices/register` | Register device |
| `POST` | `/api/devices/heartbeat` | Device heartbeat |
| `GET` | `/api/devices` | List devices |
| `GET/POST` | `/api/dns/dns-query` | DoH endpoint (RFC 8484) |
| `GET` | `/api/policies` | List policies |
| `GET` | `/api/wireguard/config/{id}` | Get WG config |

## 🔐 Security Features

- **JWT Authentication** with access/refresh tokens
- **Role-Based Access Control** (Super Admin, Admin, Analyst, User)
- **WireGuard Encryption** for all tunnel traffic
- **DNS-over-HTTPS** with policy-based filtering
- **Device Posture Checks** (encryption, antivirus, OS version)
- **Audit Logging** for all admin actions
- **Redis Token Blacklisting** for secure logout

## 📁 Project Structure

```
SecureNet-One/
├── agent/          # Go Desktop Agent
├── backend/        # FastAPI Backend
├── dashboard/      # Next.js Dashboard
├── deployment/     # Docker Compose + Nginx
├── docs/           # Documentation
├── scripts/        # Utility scripts
└── README.md
```

## 📋 Development Roadmap

- [x] Phase 1: Backend (Auth, Devices, API)
- [x] Phase 2: Policy Engine, Logging, WireGuard, DoH
- [x] Phase 3: Next.js Dashboard
- [x] Phase 4: Go Desktop Agent
- [x] Phase 5: Docker Deployment
- [ ] Phase 6: Split Tunneling
- [ ] Phase 7: Linux/macOS Agents

## 📝 License

This project is built for educational purposes as a final-year cybersecurity project.

---

Built with ❤️ inspired by [Cloudflare One](https://one.dash.cloudflare.com/)
