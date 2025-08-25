"""
Super Admin Module Models - Panel de administración global
Gestión cross-server para el dueño del bot
"""

from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SubscriptionPlan(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    VIP = "vip"


class ServerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"
    TRIAL = "trial"


# Discord Server Info
class DiscordServerInfo(BaseModel):
    guild_id: str
    guild_name: str
    owner_id: str
    owner_username: str
    member_count: int
    created_at: datetime
    subscription_plan: SubscriptionPlan
    status: ServerStatus
    last_activity: Optional[datetime] = None
    features_enabled: List[str] = []
    monthly_usage: Dict[str, int] = {}


# Subscription Management
class SubscriptionUpdate(BaseModel):
    guild_id: str
    new_plan: SubscriptionPlan
    duration_months: int = 1
    reason: Optional[str] = None


class SubscriptionHistory(BaseModel):
    id: int
    guild_id: str
    plan: SubscriptionPlan
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    upgraded_by: str
    reason: Optional[str] = None


# Global Analytics
class GlobalAnalytics(BaseModel):
    total_servers: int
    active_servers: int
    premium_servers: int
    vip_servers: int
    total_users: int
    daily_active_users: int
    monthly_revenue: float
    top_features: List[Dict[str, Any]]
    growth_metrics: Dict[str, int]
    system_health: Dict[str, float]


# Server Usage Statistics
class ServerUsageStats(BaseModel):
    guild_id: str
    guild_name: str
    commands_used_today: int
    commands_used_month: int
    active_users_today: int
    active_users_month: int
    most_used_features: List[str]
    revenue_generated: float
    last_activity: datetime


# Premium Features Configuration
class PremiumFeature(BaseModel):
    feature_id: str
    feature_name: str
    description: str
    required_plan: SubscriptionPlan
    usage_limit: Optional[int] = None
    is_active: bool = True


# Owner Authentication
class OwnerAuth(BaseModel):
    discord_user_id: str
    username: str
    discriminator: str
    avatar_url: Optional[str] = None
    access_level: str = "owner"
    login_time: datetime
    last_activity: datetime


# System Health Monitor
class SystemHealthCheck(BaseModel):
    service_name: str
    status: str  # healthy, warning, error
    response_time: float
    uptime_percentage: float
    last_check: datetime
    error_count: int
    details: Optional[Dict[str, Any]] = None


# Bot Configuration Global
class GlobalBotConfig(BaseModel):
    maintenance_mode: bool = False
    global_announcement: Optional[str] = None
    feature_flags: Dict[str, bool] = {}
    rate_limits: Dict[str, int] = {}
    emergency_shutdown: bool = False
    version: str = "2.0.0"


# Audit Trail
class AdminAction(BaseModel):
    id: int
    admin_id: str
    admin_username: str
    action_type: str  # subscription_change, server_suspend, config_update
    target_guild_id: Optional[str] = None
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str] = None


# Response Models
class GlobalDashboard(BaseModel):
    analytics: GlobalAnalytics
    recent_actions: List[AdminAction]
    system_health: List[SystemHealthCheck]
    top_servers: List[ServerUsageStats]
    alerts: List[str] = []


class ServerManagement(BaseModel):
    servers: List[DiscordServerInfo]
    total_count: int
    filter_applied: Optional[str] = None
    subscription_summary: Dict[str, int]


class SubscriptionManagement(BaseModel):
    active_subscriptions: List[SubscriptionHistory]
    revenue_summary: Dict[str, float]
    upcoming_renewals: List[DiscordServerInfo]
    expired_subscriptions: List[DiscordServerInfo]


# Validators
class CreateServerOverride(BaseModel):
    guild_id: str
    subscription_plan: SubscriptionPlan
    duration_months: int = 1
    reason: str
    
    @validator('guild_id')
    def validate_guild_id(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Guild ID must be valid Discord snowflake')
        return v


class ServerActionBulk(BaseModel):
    guild_ids: List[str]
    action: str  # suspend, activate, upgrade, downgrade
    reason: str
    new_plan: Optional[SubscriptionPlan] = None
    
    @validator('guild_ids')
    def validate_guild_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Must specify at least one server')
        if len(v) > 50:
            raise ValueError('Cannot process more than 50 servers at once')
        return v