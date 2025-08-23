"""
SQLAlchemy models for admin panel
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base

class AdminUser(Base):
    """Admin user model"""
    __tablename__ = "admin_users"
    
    id = Column(String(32), primary_key=True, index=True)
    discord_id = Column(String(20), unique=True, index=True, nullable=False)
    username = Column(String(32), nullable=False)
    discriminator = Column(String(4), nullable=False)
    avatar_hash = Column(String(32), nullable=True)
    email = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default="viewer")
    status = Column(String(20), nullable=False, default="active")
    permissions = Column(Text, nullable=False, default="[]")  # JSON array
    guilds = Column(Text, nullable=False, default="[]")  # JSON array
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    sessions = relationship("AdminSession", back_populates="user")
    audit_logs = relationship("AdminAuditLog", back_populates="user")

class AdminSession(Base):
    """Admin session model"""
    __tablename__ = "admin_sessions"
    
    id = Column(String(32), primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("admin_users.id"), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    last_activity = Column(DateTime, nullable=False, default=func.now())
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    user = relationship("AdminUser", back_populates="sessions")

class AdminAuditLog(Base):
    """Admin audit log model"""
    __tablename__ = "admin_audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("admin_users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("AdminUser", back_populates="audit_logs")

class AdminBotConfig(Base):
    """Bot configuration model"""
    __tablename__ = "admin_bot_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(20), nullable=False, index=True)
    config_key = Column(String(100), nullable=False)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(20), nullable=False, default="string")  # string, integer, boolean, json
    description = Column(String(500), nullable=True)
    category = Column(String(50), nullable=False, default="general")
    is_encrypted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    updated_by = Column(String(32), ForeignKey("admin_users.id"), nullable=False)

class AdminFameReward(Base):
    """Fame rewards configuration model"""
    __tablename__ = "admin_fame_rewards"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(20), nullable=False, index=True)
    reward_name = Column(String(100), nullable=False)
    fame_cost = Column(Integer, nullable=False)
    reward_type = Column(String(20), nullable=False)  # role, item, money, custom
    reward_value = Column(Text, nullable=False)  # JSON with reward details
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    max_purchases = Column(Integer, nullable=True)  # NULL = unlimited
    cooldown_hours = Column(Integer, nullable=False, default=0)
    required_role = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(32), ForeignKey("admin_users.id"), nullable=False)

class AdminTaxiConfig(Base):
    """Taxi system configuration model"""
    __tablename__ = "admin_taxi_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(20), nullable=False, index=True)
    config_type = Column(String(50), nullable=False)  # route, pricing, vehicle, general
    config_data = Column(Text, nullable=False)  # JSON configuration
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(32), ForeignKey("admin_users.id"), nullable=False)

class AdminBankingConfig(Base):
    """Banking system configuration model"""
    __tablename__ = "admin_banking_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(20), nullable=False, index=True)
    bank_name = Column(String(100), nullable=False)
    interest_rate = Column(String(10), nullable=False)  # Stored as string for precision
    min_deposit = Column(Integer, nullable=False, default=1000)
    max_deposit = Column(Integer, nullable=True)
    withdrawal_fee = Column(String(10), nullable=False, default="0")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(32), ForeignKey("admin_users.id"), nullable=False)

class AdminMechanicConfig(Base):
    """Mechanic system configuration model"""
    __tablename__ = "admin_mechanic_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(20), nullable=False, index=True)
    service_type = Column(String(50), nullable=False)
    service_name = Column(String(100), nullable=False)
    base_price = Column(Integer, nullable=False)
    repair_time_minutes = Column(Integer, nullable=False, default=30)
    required_items = Column(Text, nullable=True)  # JSON array of required items
    success_rate = Column(String(5), nullable=False, default="100")  # Percentage as string
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(32), ForeignKey("admin_users.id"), nullable=False)

class AdminAnalytics(Base):
    """Analytics data model"""
    __tablename__ = "admin_analytics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(20), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(String(100), nullable=False)
    metric_type = Column(String(20), nullable=False)  # counter, gauge, histogram
    dimensions = Column(Text, nullable=True)  # JSON with additional dimensions
    timestamp = Column(DateTime, nullable=False, default=func.now())

class AdminNotification(Base):
    """Admin notifications model"""
    __tablename__ = "admin_notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("admin_users.id"), nullable=True)  # NULL = broadcast
    guild_id = Column(String(20), nullable=True)  # NULL = system-wide
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(20), nullable=False, default="info")  # info, warning, error, success
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    read_at = Column(DateTime, nullable=True)

class AdminSystemStatus(Base):
    """System status model"""
    __tablename__ = "admin_system_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    component = Column(String(50), nullable=False, unique=True)  # bot, database, api, etc.
    status = Column(String(20), nullable=False, default="unknown")  # online, offline, degraded, unknown
    last_check = Column(DateTime, nullable=False, default=func.now())
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON with additional status info
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())