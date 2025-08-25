"""
User Management Module - Pydantic Models
Sistema completo de usuarios, roles, permisos y auditoría
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Enums for validation
class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write" 
    DELETE = "delete"
    ADMIN = "admin"

class ModuleName(str, Enum):
    FAME = "fame"
    BANKING = "banking"
    TAXI = "taxi"
    MECHANIC = "mechanic"
    ANALYTICS = "analytics"
    USERS = "users"
    LOGS = "logs"
    SETTINGS = "settings"

class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    VIEW = "view"
    EXPORT = "export"

# Core Models

class Permission(BaseModel):
    """Individual permission model"""
    id: Optional[int] = None
    permission_name: str
    display_name: str
    description: Optional[str] = None
    module_name: ModuleName
    permission_type: PermissionType
    created_at: Optional[datetime] = None

class PermissionCreate(BaseModel):
    """Permission creation model"""
    permission_name: str = Field(..., min_length=3, max_length=100)
    display_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    module_name: ModuleName
    permission_type: PermissionType

class Role(BaseModel):
    """Role model with permissions"""
    id: Optional[int] = None
    role_name: str
    display_name: str
    description: Optional[str] = None
    color: str = "#6366f1"
    is_system_role: bool = False
    permissions: List[Permission] = []
    user_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RoleCreate(BaseModel):
    """Role creation model"""
    role_name: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-z_]+$")
    display_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: str = Field("#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")
    permission_ids: List[int] = []

class RoleUpdate(BaseModel):
    """Role update model"""
    display_name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    permission_ids: Optional[List[int]] = None

class User(BaseModel):
    """Admin user model"""
    id: Optional[int] = None
    discord_user_id: str
    discord_username: str
    discord_discriminator: Optional[str] = None
    discord_avatar: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None
    role_id: int
    role: Optional[Role] = None
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    login_count: int = 0
    permissions: List[Permission] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserCreate(BaseModel):
    """User creation model"""
    discord_user_id: str = Field(..., min_length=17, max_length=20)
    discord_username: str = Field(..., min_length=2, max_length=32)
    discord_discriminator: Optional[str] = Field(None, pattern=r"^\d{4}$")
    discord_avatar: Optional[str] = None
    email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    display_name: Optional[str] = Field(None, max_length=100)
    role_id: int = Field(..., gt=0)

class UserUpdate(BaseModel):
    """User update model"""
    discord_username: Optional[str] = Field(None, min_length=2, max_length=32)
    discord_discriminator: Optional[str] = Field(None, pattern=r"^\d{4}$")
    discord_avatar: Optional[str] = None
    email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    display_name: Optional[str] = Field(None, max_length=100)
    role_id: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None

class SessionInfo(BaseModel):
    """Session information model"""
    id: Optional[int] = None
    user_id: int
    session_token: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

class AuditLogEntry(BaseModel):
    """Audit log entry model"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    user: Optional[User] = None
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[int] = None
    created_at: Optional[datetime] = None

class AuditLogCreate(BaseModel):
    """Audit log creation model"""
    user_id: Optional[int] = None
    action: AuditAction
    resource_type: str = Field(..., max_length=100)
    resource_id: Optional[str] = Field(None, max_length=100)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[int] = None

# Response Models

class UserSummary(BaseModel):
    """User summary for lists"""
    id: int
    discord_username: str
    display_name: Optional[str]
    role_name: str
    role_display_name: str
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime]

class RoleSummary(BaseModel):
    """Role summary for lists"""
    id: int
    role_name: str
    display_name: str
    color: str
    permission_count: int
    user_count: int
    is_system_role: bool

class PermissionsByModule(BaseModel):
    """Permissions grouped by module"""
    module_name: ModuleName
    module_display_name: str
    permissions: List[Permission]

class UserPermissions(BaseModel):
    """User permissions response"""
    user_id: int
    role_id: int
    role_name: str
    permissions: List[str]  # List of permission names
    modules: List[PermissionsByModule]

class SystemStats(BaseModel):
    """System statistics"""
    total_users: int
    active_users: int
    total_roles: int
    total_permissions: int
    recent_logins: int
    pending_sessions: int

# Authentication Models (for future OAuth2 implementation)

class LoginRequest(BaseModel):
    """Login request (for testing without Discord OAuth)"""
    discord_user_id: str
    password: Optional[str] = None  # For testing only

class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User
    permissions: List[str]

class TokenData(BaseModel):
    """Token data for JWT"""
    user_id: int
    discord_user_id: str
    role_id: int
    permissions: List[str]
    session_id: int

# Validation and utility functions

def validate_discord_user_id(discord_user_id: str) -> bool:
    """Validate Discord user ID format"""
    return discord_user_id.isdigit() and len(discord_user_id) in [17, 18, 19, 20]

def validate_permission_name(permission_name: str) -> bool:
    """Validate permission name format (module.action)"""
    parts = permission_name.split('.')
    return len(parts) == 2 and all(part.isalpha() or '_' in part for part in parts)

# Custom validators removed - using Field validation instead

# Search and filter models

class UserFilter(BaseModel):
    """User search/filter parameters"""
    search: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    module_permission: Optional[ModuleName] = None

class AuditLogFilter(BaseModel):
    """Audit log search/filter parameters"""
    user_id: Optional[int] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(50, le=1000)
    offset: int = Field(0, ge=0)