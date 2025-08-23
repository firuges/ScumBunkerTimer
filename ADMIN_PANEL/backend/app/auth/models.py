"""
Authentication models and schemas
"""

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """User roles enum"""
    SUPER_ADMIN = "super_admin"
    GUILD_ADMIN = "guild_admin" 
    MODERATOR = "moderator"
    VIEWER = "viewer"

class UserStatus(str, Enum):
    """User status enum"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"

# Request/Response Models
class DiscordUser(BaseModel):
    """Discord user info from OAuth2"""
    id: str
    username: str
    discriminator: str
    avatar: Optional[str] = None
    email: Optional[str] = None

class LoginRequest(BaseModel):
    """Discord OAuth2 login request"""
    code: str
    state: Optional[str] = None

class LoginResponse(BaseModel):
    """Login response with token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: 'UserProfile'

class UserProfile(BaseModel):
    """User profile information"""
    id: str
    discord_id: str
    username: str
    discriminator: str
    avatar_url: Optional[str] = None
    role: UserRole
    status: UserStatus
    guilds: List[str] = []
    permissions: List[str] = []
    created_at: datetime
    last_login: Optional[datetime] = None

class TokenData(BaseModel):
    """JWT token data"""
    user_id: str
    discord_id: str
    role: UserRole
    guilds: List[str] = []
    exp: int

class UserUpdate(BaseModel):
    """User update request"""
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    permissions: Optional[List[str]] = None

class PasswordChangeRequest(BaseModel):
    """Password change request (if needed for API keys)"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str

class LogoutRequest(BaseModel):
    """Logout request"""
    token: str
    logout_all_devices: bool = False

# Database Models (for reference, actual SQLAlchemy models will be separate)
class AdminUserDB(BaseModel):
    """Admin user database model schema"""
    id: str
    discord_id: str
    username: str
    discriminator: str
    avatar_hash: Optional[str] = None
    email: Optional[str] = None
    role: UserRole
    status: UserStatus
    permissions: str  # JSON string of permissions list
    guilds: str  # JSON string of guild IDs
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = 0

class AdminSessionDB(BaseModel):
    """Admin session database model schema"""
    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    created_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True

# Update forward references
LoginResponse.model_rebuild()