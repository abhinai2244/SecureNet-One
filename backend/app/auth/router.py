"""
SecureNet One - Auth Router
API endpoints for authentication and user management.
"""

from fastapi import APIRouter, Depends

from app.auth.schemas import (
    LoginResponse,
    MessageResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserListResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserRoleUpdateRequest,
)
from app.auth.service import AuthService
from app.core.security import require_admin, require_super_admin
from app.shared.dependencies import CurrentUserId, DbSession, Pagination

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(data: UserRegisterRequest, db: DbSession):
    """Register a new user account."""
    service = AuthService(db)
    return await service.register(data)


@router.post("/login", response_model=LoginResponse)
async def login(data: UserLoginRequest, db: DbSession):
    """Authenticate and receive JWT tokens."""
    service = AuthService(db)
    return await service.login(data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: TokenRefreshRequest, db: DbSession):
    """Refresh access token using refresh token."""
    service = AuthService(db)
    return await service.refresh_token(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(user_id: CurrentUserId, db: DbSession):
    """Get the current authenticated user's profile."""
    service = AuthService(db)
    return await service.get_current_user(user_id)


@router.post("/logout", response_model=MessageResponse)
async def logout(user_id: CurrentUserId):
    """Logout and invalidate the current session."""
    # In a production app, we'd blacklist the token in Redis
    return MessageResponse(message="Successfully logged out")


# ── Admin User Management ────────────────────────────────────────

@router.get("/users", response_model=UserListResponse)
async def list_users(
    db: DbSession,
    pagination: Pagination,
    _admin_id: str = Depends(require_admin),
):
    """List all users (admin only)."""
    service = AuthService(db)
    users, total = await service.get_all_users(pagination.offset, pagination.limit)
    return UserListResponse(
        users=users,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    data: UserRoleUpdateRequest,
    db: DbSession,
    _admin_id: str = Depends(require_super_admin),
):
    """Update a user's role (super admin only)."""
    service = AuthService(db)
    return await service.update_user_role(user_id, data.role)
