# SecureNet One — Installation Guide

## Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.10+ | Backend API |
| Node.js | 20+ | Dashboard |
| Go | 1.21+ | Desktop Agent |
| Docker Desktop | Latest | PostgreSQL, Redis |
| Git | Latest | Version control |

## Step-by-Step Setup

### 1. Clone the Repository
```bash
git clone https://github.com/abhinai2244/SecureNet-One.git
cd SecureNet-One
```

### 2. Start Database Services
```bash
cd deployment
docker compose up postgres redis -d
```

Wait for both services to be healthy:
```bash
docker compose ps
```

### 3. Configure Backend
```bash
cd backend

# Copy and edit environment variables
cp .env .env.local   # (optional: customize settings)

# Install Python dependencies
pip install -r requirements.txt

# Create database tables
python -c "
import asyncio
from app.core.database import engine, Base
from app.auth.models import User
from app.devices.models import Device
from app.policies.models import Policy
from app.logs.models import DeviceLog, DnsLog, AuditLog
from app.wireguard.models import WireGuardPeer

async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Tables created!')

asyncio.run(create())
"

# Seed demo data (optional)
python scripts/seed_database.py

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

Backend is now running at: http://localhost:8000
- API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Start Dashboard
```bash
cd dashboard
npm install
npm run dev
```

Dashboard is now running at: http://localhost:3000

### 5. Build Desktop Agent (Optional)
```bash
cd agent
go build -o securenet.exe ./cmd/securenet/

# Run with credentials
./securenet.exe \
  --server http://localhost:8000/api \
  --email admin@securenet.local \
  --password admin123456 \
  --auto-connect
```

### 6. Full Docker Deployment (Alternative)
```bash
cd deployment
docker compose up --build -d
```

Access via Nginx: http://localhost:8080

## Demo Credentials

| Email | Password | Role |
|-------|----------|------|
| admin@securenet.local | admin123456 | Super Admin |
| analyst@securenet.local | analyst123456 | Analyst |
| user@securenet.local | user12345678 | User |

> **Note**: Run `python scripts/seed_database.py` from the `backend/` directory to create these accounts.

## Troubleshooting

### Backend won't start
- Ensure PostgreSQL is running: `docker compose ps`
- Check `.env` has correct `DATABASE_URL`
- Run from the `backend/` directory (not `backend/app/`)

### Dashboard shows empty data
- Ensure backend is running on port 8000
- Run the seed script to populate demo data
- Check browser console for API errors

### Docker issues
- Ensure Docker Desktop is running
- Try `docker compose down -v` then `docker compose up -d` for fresh start
