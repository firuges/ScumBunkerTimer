"""
Authentication utilities and helpers
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from passlib.hash import bcrypt
import aiohttp
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthUtils:
    """Authentication utility functions"""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.PyJWTError:
            return None
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)

class DiscordAPI:
    """Discord API client for OAuth2"""
    
    BASE_URL = "https://discord.com/api/v10"
    
    @classmethod
    async def exchange_code(cls, code: str) -> Optional[Dict[str, Any]]:
        """Exchange OAuth2 code for access token"""
        data = {
            'client_id': settings.DISCORD_CLIENT_ID,
            'client_secret': settings.DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.DISCORD_REDIRECT_URI,
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{cls.BASE_URL}/oauth2/token",
                    data=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Discord token exchange failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error exchanging Discord code: {e}")
            return None
    
    @classmethod
    async def get_user_info(cls, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user info from Discord API"""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{cls.BASE_URL}/users/@me",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Discord user info failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting Discord user info: {e}")
            return None
    
    @classmethod
    async def get_user_guilds(cls, access_token: str) -> List[Dict[str, Any]]:
        """Get user's guilds from Discord API"""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{cls.BASE_URL}/users/@me/guilds",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        guilds = await response.json()
                        # Filter guilds where user has admin permissions
                        admin_guilds = [
                            guild for guild in guilds 
                            if int(guild.get('permissions', 0)) & 0x8  # ADMINISTRATOR permission
                        ]
                        return admin_guilds
                    else:
                        logger.error(f"Discord guilds fetch failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting Discord guilds: {e}")
            return []
    
    @classmethod
    def get_avatar_url(cls, user_id: str, avatar_hash: Optional[str]) -> Optional[str]:
        """Get user avatar URL"""
        if not avatar_hash:
            return None
        
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"

class PermissionChecker:
    """Permission checking utilities"""
    
    # Define permission hierarchy
    ROLE_HIERARCHY = {
        "super_admin": 4,
        "guild_admin": 3,
        "moderator": 2,
        "viewer": 1
    }
    
    # Define module permissions
    MODULE_PERMISSIONS = {
        "fame_points": ["guild_admin", "super_admin"],
        "taxi_system": ["guild_admin", "super_admin"],
        "banking_system": ["guild_admin", "super_admin"],
        "mechanics_system": ["moderator", "guild_admin", "super_admin"],
        "analytics": ["guild_admin", "super_admin"],
        "user_management": ["super_admin"],
        "audit_logs": ["guild_admin", "super_admin"],
        "bot_config": ["super_admin"]
    }
    
    @classmethod
    def has_permission(cls, user_role: str, required_permission: str) -> bool:
        """Check if user role has required permission"""
        allowed_roles = cls.MODULE_PERMISSIONS.get(required_permission, [])
        return user_role in allowed_roles
    
    @classmethod
    def can_access_module(cls, user_role: str, module_name: str) -> bool:
        """Check if user can access a module"""
        return cls.has_permission(user_role, module_name)
    
    @classmethod
    def is_higher_role(cls, role1: str, role2: str) -> bool:
        """Check if role1 is higher than role2"""
        level1 = cls.ROLE_HIERARCHY.get(role1, 0)
        level2 = cls.ROLE_HIERARCHY.get(role2, 0)
        return level1 > level2
    
    @classmethod
    def can_manage_user(cls, admin_role: str, target_role: str) -> bool:
        """Check if admin can manage target user"""
        return cls.is_higher_role(admin_role, target_role)