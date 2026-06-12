"""
SecureNet One - FastAPI Application Factory
Main entry point for the backend server.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.redis import close_redis
from app.shared.middleware import setup_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("securenet")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown events."""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📡 Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured'}")
    logger.info(f"🔑 JWT Algorithm: {settings.JWT_ALGORITHM}")
    yield
    logger.info("🛑 Shutting down...")
    await close_redis()
    logger.info("✅ Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "SecureNet One - Zero Trust Security Platform API. "
            "A Cloudflare One / WARP-inspired security platform with "
            "WireGuard tunneling, DNS-over-HTTPS, device posture monitoring, "
            "and centralized policy management."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Setup middleware (CORS, logging)
    setup_middleware(app)

    # Register routers
    from app.auth.router import router as auth_router
    from app.devices.router import router as devices_router
    from app.policies.router import router as policies_router
    from app.logs.router import router as logs_router
    from app.wireguard.router import router as wireguard_router
    from app.dns.router import router as dns_router

    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(devices_router, prefix=settings.API_PREFIX)
    app.include_router(policies_router, prefix=settings.API_PREFIX)
    app.include_router(logs_router, prefix=settings.API_PREFIX)
    app.include_router(wireguard_router, prefix=settings.API_PREFIX)
    app.include_router(dns_router, prefix=settings.API_PREFIX)

    @app.get("/", tags=["Health"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "operational",
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()
