"""
SecureNet One - Database Seed Script
Creates demo users, devices, policies, and sample logs for testing.

Usage:
    cd backend
    python scripts/seed_database.py
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.database import engine, async_session, Base
from app.auth.models import User, UserRole
from app.devices.models import Device, DeviceStatus
from app.policies.models import Policy, PolicyType
from app.logs.models import DeviceLog, DnsLog, DeviceEventType, DnsAction
from app.core.security import hash_password


async def seed():
    """Seed the database with demo data."""
    print("🌱 Seeding SecureNet One database...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created")

    async with async_session() as session:
        # ── Users ────────────────────────────────────────────────
        users = [
            User(
                email="admin@securenet.local",
                password_hash=hash_password("admin123456"),
                full_name="Admin User",
                role=UserRole.SUPER_ADMIN,
            ),
            User(
                email="analyst@securenet.local",
                password_hash=hash_password("analyst123456"),
                full_name="Security Analyst",
                role=UserRole.ANALYST,
            ),
            User(
                email="user@securenet.local",
                password_hash=hash_password("user12345678"),
                full_name="Regular User",
                role=UserRole.USER,
            ),
        ]
        for u in users:
            session.add(u)
        await session.flush()
        print(f"✅ Created {len(users)} users")

        admin = users[0]
        regular = users[2]

        # ── Devices ──────────────────────────────────────────────
        devices = [
            Device(
                user_id=admin.id,
                device_name="Admin Workstation",
                hostname="ADMIN-PC",
                os="windows",
                os_version="Windows 11 Pro 23H2",
                agent_version="1.0.0",
                status=DeviceStatus.ONLINE,
                assigned_ip="10.0.0.2",
                last_ip="192.168.1.100",
                last_seen=datetime.now(timezone.utc),
                disk_encrypted=True,
                antivirus_active=True,
                cpu_info="AMD Ryzen 7 5800X (16 cores)",
                ram_bytes=34359738368,  # 32 GB
            ),
            Device(
                user_id=admin.id,
                device_name="Admin Laptop",
                hostname="ADMIN-LAPTOP",
                os="windows",
                os_version="Windows 11 Home 22H2",
                agent_version="1.0.0",
                status=DeviceStatus.OFFLINE,
                assigned_ip="10.0.0.3",
                last_ip="10.42.0.5",
                last_seen=datetime.now(timezone.utc) - timedelta(hours=3),
                disk_encrypted=True,
                antivirus_active=True,
                cpu_info="Intel i7-12700H (14 cores)",
                ram_bytes=17179869184,  # 16 GB
            ),
            Device(
                user_id=regular.id,
                device_name="User Desktop",
                hostname="USER-DESKTOP",
                os="windows",
                os_version="Windows 10 Pro 22H2",
                agent_version="0.9.0",
                status=DeviceStatus.WARNING,
                assigned_ip="10.0.0.4",
                last_ip="192.168.1.150",
                last_seen=datetime.now(timezone.utc) - timedelta(minutes=15),
                disk_encrypted=False,
                antivirus_active=False,
                cpu_info="Intel i5-10400 (6 cores)",
                ram_bytes=8589934592,  # 8 GB
            ),
        ]
        for d in devices:
            session.add(d)
        await session.flush()
        print(f"✅ Created {len(devices)} devices")

        # ── Policies ─────────────────────────────────────────────
        policies = [
            Policy(
                name="Block Malware Domains",
                description="Blocks known malware and phishing domains",
                type=PolicyType.DNS,
                rules={
                    "blocked_domains": [
                        "malware-site.example.com",
                        "*.phishing.net",
                        "tracking.ad-network.com",
                        "*.cryptominer.xyz",
                    ],
                    "blocked_categories": ["malware", "phishing", "cryptomining"],
                },
                enabled=True,
                priority=10,
                created_by=admin.id,
            ),
            Policy(
                name="Block Social Media",
                description="Restricts access to social media during work hours",
                type=PolicyType.DNS,
                rules={
                    "blocked_domains": [
                        "*.tiktok.com",
                        "*.facebook.com",
                        "*.instagram.com",
                    ],
                    "blocked_categories": ["social_media"],
                },
                enabled=False,
                priority=50,
                created_by=admin.id,
            ),
            Policy(
                name="Full Tunnel Mode",
                description="Route all traffic through VPN tunnel",
                type=PolicyType.TUNNEL,
                rules={
                    "mode": "full",
                    "allowed_ips": "0.0.0.0/0, ::/0",
                },
                enabled=True,
                priority=1,
                created_by=admin.id,
            ),
            Policy(
                name="Require Disk Encryption",
                description="Devices must have disk encryption enabled",
                type=PolicyType.POSTURE,
                rules={
                    "require_disk_encryption": True,
                    "require_antivirus": True,
                    "min_os_version": "10.0",
                },
                enabled=True,
                priority=20,
                created_by=admin.id,
            ),
        ]
        for p in policies:
            session.add(p)
        await session.flush()
        print(f"✅ Created {len(policies)} policies")

        # ── Device Logs ──────────────────────────────────────────
        now = datetime.now(timezone.utc)
        device_logs = []
        for i, device in enumerate(devices):
            for j in range(5):
                device_logs.append(DeviceLog(
                    device_id=device.id,
                    event_type=DeviceEventType.CONNECT if j % 3 == 0 else (
                        DeviceEventType.HEARTBEAT if j % 3 == 1 else DeviceEventType.DISCONNECT
                    ),
                    payload={"agent_version": device.agent_version},
                    source_ip=device.last_ip,
                    timestamp=now - timedelta(hours=i * 2, minutes=j * 30),
                ))
        for log in device_logs:
            session.add(log)
        print(f"✅ Created {len(device_logs)} device logs")

        # ── DNS Logs ─────────────────────────────────────────────
        dns_queries = [
            ("google.com", "A", DnsAction.ALLOW),
            ("github.com", "A", DnsAction.ALLOW),
            ("malware-site.example.com", "A", DnsAction.BLOCK),
            ("docs.python.org", "A", DnsAction.ALLOW),
            ("tracking.ad-network.com", "A", DnsAction.BLOCK),
            ("stackoverflow.com", "A", DnsAction.ALLOW),
            ("*.phishing.net", "A", DnsAction.BLOCK),
            ("api.openai.com", "A", DnsAction.ALLOW),
            ("*.cryptominer.xyz", "AAAA", DnsAction.BLOCK),
            ("cloudflare.com", "A", DnsAction.ALLOW),
        ]
        dns_logs = []
        for i, (domain, qtype, action) in enumerate(dns_queries):
            dns_logs.append(DnsLog(
                device_id=devices[i % len(devices)].id,
                query_name=domain,
                query_type=qtype,
                response_code="NXDOMAIN" if action == DnsAction.BLOCK else "NOERROR",
                action=action,
                response_time_ms=5 + (i * 3),
                timestamp=now - timedelta(minutes=i * 10),
            ))
        for log in dns_logs:
            session.add(log)
        print(f"✅ Created {len(dns_logs)} DNS logs")

        await session.commit()

    print()
    print("═" * 50)
    print("🎉 Database seeded successfully!")
    print("═" * 50)
    print()
    print("Demo Accounts:")
    print("  admin@securenet.local / admin123456 (Super Admin)")
    print("  analyst@securenet.local / analyst123456 (Analyst)")
    print("  user@securenet.local / user12345678 (User)")
    print()


if __name__ == "__main__":
    asyncio.run(seed())
