"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import logging
import json

from app.core.database import get_db, db_manager
from app.core.config import settings
from .models import (
    LoginRequest, LoginResponse, UserProfile, TokenData, 
    UserUpdate, RefreshTokenRequest, LogoutRequest,
    UserRole, UserStatus
)
from .utils import AuthUtils, DiscordAPI, PermissionChecker

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserProfile:
    """Get current authenticated user"""
    token = credentials.credentials
    
    # Verify token
    payload = AuthUtils.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    query = "SELECT * FROM admin_users WHERE id = ? AND status = 'active'"
    result = await db_manager.execute_query(query, (user_id,))
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    user_data = result[0]
    
    return UserProfile(
        id=user_data['id'],
        discord_id=user_data['discord_id'],
        username=user_data['username'],
        discriminator=user_data['discriminator'],
        avatar_url=DiscordAPI.get_avatar_url(
            user_data['discord_id'], 
            user_data['avatar_hash']
        ),
        role=UserRole(user_data['role']),
        status=UserStatus(user_data['status']),
        guilds=json.loads(user_data.get('guilds', '[]')),
        permissions=json.loads(user_data.get('permissions', '[]')),
        created_at=datetime.fromisoformat(user_data['created_at']),
        last_login=datetime.fromisoformat(user_data['last_login']) if user_data['last_login'] else None
    )

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(user: UserProfile = Depends(get_current_user)):
        if not PermissionChecker.has_permission(user.role.value, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return user
    return permission_checker

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Discord OAuth2 login"""
    try:
        # Exchange code for access token
        token_data = await DiscordAPI.exchange_code(request.code)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange Discord code"
            )
        
        discord_token = token_data['access_token']
        
        # Get user info from Discord
        user_info = await DiscordAPI.get_user_info(discord_token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get Discord user info"
            )
        
        # Get user guilds
        guilds = await DiscordAPI.get_user_guilds(discord_token)
        guild_ids = [guild['id'] for guild in guilds]
        
        discord_id = user_info['id']
        username = user_info['username']
        discriminator = user_info['discriminator']
        avatar_hash = user_info.get('avatar')
        email = user_info.get('email')
        
        # Check if user exists in database
        query = "SELECT * FROM admin_users WHERE discord_id = ?"
        result = await db_manager.execute_query(query, (discord_id,))
        
        if result:
            # Update existing user
            user_data = result[0]
            update_query = """
                UPDATE admin_users 
                SET username = ?, discriminator = ?, avatar_hash = ?, 
                    email = ?, guilds = ?, last_login = ?, login_count = login_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE discord_id = ?
            """
            await db_manager.execute_command(
                update_query,
                (username, discriminator, avatar_hash, email, 
                 json.dumps(guild_ids), datetime.utcnow().isoformat(), discord_id)
            )
            
            user_id = user_data['id']
            role = UserRole(user_data['role'])
            status = UserStatus(user_data['status'])
            
        else:
            # Create new user (default viewer role)
            user_id = AuthUtils.generate_session_id()
            role = UserRole.VIEWER
            status = UserStatus.ACTIVE
            
            insert_query = """
                INSERT INTO admin_users 
                (id, discord_id, username, discriminator, avatar_hash, email, 
                 role, status, permissions, guilds, created_at, updated_at, 
                 last_login, login_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """
            await db_manager.execute_command(
                insert_query,
                (user_id, discord_id, username, discriminator, avatar_hash, email,
                 role.value, status.value, json.dumps([]), json.dumps(guild_ids),
                 datetime.utcnow().isoformat(), datetime.utcnow().isoformat(),
                 datetime.utcnow().isoformat())
            )
        
        # Check if user is suspended or banned
        if status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {status.value}"
            )
        
        # Create JWT token
        token_payload = {
            "user_id": user_id,
            "discord_id": discord_id,
            "role": role.value,
            "guilds": guild_ids
        }
        
        access_token = AuthUtils.create_access_token(token_payload)
        
        # Create session record
        session_id = AuthUtils.generate_session_id()
        token_hash = AuthUtils.hash_token(access_token)
        
        session_query = """
            INSERT INTO admin_sessions 
            (id, user_id, token_hash, expires_at, created_at, last_activity, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """
        expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        await db_manager.execute_command(
            session_query,
            (session_id, user_id, token_hash, expires_at.isoformat(),
             datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
        )
        
        # Create user profile
        user_profile = UserProfile(
            id=user_id,
            discord_id=discord_id,
            username=username,
            discriminator=discriminator,
            avatar_url=DiscordAPI.get_avatar_url(discord_id, avatar_hash),
            role=role,
            status=status,
            guilds=guild_ids,
            permissions=[],  # Will be populated based on role
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
        logger.info(f"User {username}#{discriminator} logged in successfully")
        
        return LoginResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/logout")
async def logout(
    request: LogoutRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Logout user"""
    try:
        token_hash = AuthUtils.hash_token(request.token)
        
        if request.logout_all_devices:
            # Deactivate all user sessions
            query = "UPDATE admin_sessions SET is_active = 0 WHERE user_id = ?"
            await db_manager.execute_command(query, (current_user.id,))
        else:
            # Deactivate current session
            query = "UPDATE admin_sessions SET is_active = 0 WHERE token_hash = ?"
            await db_manager.execute_command(query, (token_hash,))
        
        logger.info(f"User {current_user.username} logged out")
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserProfile)
async def get_current_user_info(current_user: UserProfile = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@router.get("/permissions")
async def get_user_permissions(current_user: UserProfile = Depends(get_current_user)):
    """Get user permissions and accessible modules"""
    permissions = {}
    
    for module, required_roles in PermissionChecker.MODULE_PERMISSIONS.items():
        permissions[module] = current_user.role.value in required_roles
    
    return {
        "user": current_user.username,
        "role": current_user.role.value,
        "permissions": permissions,
        "modules": [
            module for module, has_access in permissions.items() 
            if has_access
        ]
    }

@router.get("/discord-url")
async def get_discord_oauth_url():
    """Get Discord OAuth2 authorization URL"""
    from app.core.config import get_discord_oauth_url
    return {"url": get_discord_oauth_url()}

# Admin user management routes (require super_admin permission)
@router.get("/users")
async def list_users(
    current_user: UserProfile = Depends(require_permission("user_management"))
):
    """List all admin users"""
    query = """
        SELECT id, discord_id, username, discriminator, role, status, 
               created_at, last_login, login_count
        FROM admin_users 
        ORDER BY created_at DESC
    """
    
    users = await db_manager.execute_query(query)
    return {"users": users}

@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: UserProfile = Depends(require_permission("user_management"))
):
    """Update user role and permissions"""
    # Get target user
    query = "SELECT role FROM admin_users WHERE id = ?"
    result = await db_manager.execute_query(query, (user_id,))
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    target_role = result[0]['role']
    
    # Check if current user can manage target user
    if not PermissionChecker.can_manage_user(current_user.role.value, target_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot manage user with equal or higher role"
        )
    
    # Update user
    update_fields = []
    params = []
    
    if update_data.role:
        update_fields.append("role = ?")
        params.append(update_data.role.value)
    
    if update_data.status:
        update_fields.append("status = ?")
        params.append(update_data.status.value)
    
    if update_data.permissions:
        update_fields.append("permissions = ?")
        params.append(json.dumps(update_data.permissions))
    
    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)
        
        query = f"UPDATE admin_users SET {', '.join(update_fields)} WHERE id = ?"
        await db_manager.execute_command(query, tuple(params))
    
    return {"message": "User updated successfully"}