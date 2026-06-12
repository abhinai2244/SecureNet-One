"""
SecureNet One - Auth Service
Business logic for authentication and user management.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import UserRole
from app.auth.repository import UserRepository
from app.auth.schemas import (
    LoginResponse,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.shared.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
)

settings = get_settings()


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register(self, data: UserRegisterRequest) -> LoginResponse:
        """Register a new user and return tokens."""
        # Check if email already exists
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise AlreadyExistsException("User", "email")

        # Create user
        hashed = hash_password(data.password)
        user = await self.repo.create(
            email=data.email,
            password_hash=hashed,
            full_name=data.full_name,
        )

        # Generate tokens
        tokens = self._create_tokens(str(user.id), user.role.value)

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def login(self, email: str, password: str) -> LoginResponse:
        """Authenticate user and return tokens."""
        user = await self.repo.get_by_email(email)
        if not user:
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        # Generate tokens
        tokens = self._create_tokens(str(user.id), user.role.value)

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise BadRequestException("Invalid token type")

        user_id = payload.get("sub")
        user = await self.repo.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or deactivated")

        return self._create_tokens(str(user.id), user.role.value)

    async def get_current_user(self, user_id: str) -> UserResponse:
        """Get current user profile."""
        user = await self.repo.get_by_id(UUID(user_id))
        if not user:
            raise NotFoundException("User", user_id)
        return UserResponse.model_validate(user)

    async def get_all_users(
        self, offset: int = 0, limit: int = 20
    ) -> tuple[list[UserResponse], int]:
        """Get all users (admin only)."""
        users, total = await self.repo.get_all(offset, limit)
        return [UserResponse.model_validate(u) for u in users], total

    async def update_user_role(
        self, user_id: str, role: str
    ) -> UserResponse:
        """Update a user's role (super admin only)."""
        user = await self.repo.get_by_id(UUID(user_id))
        if not user:
            raise NotFoundException("User", user_id)

        user = await self.repo.update(user, role=UserRole(role))
        return UserResponse.model_validate(user)

    def _create_tokens(self, user_id: str, role: str) -> TokenResponse:
        """Create access and refresh token pair."""
        access_token = create_access_token(user_id, role)
        refresh_token = create_refresh_token(user_id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
