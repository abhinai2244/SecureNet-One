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
