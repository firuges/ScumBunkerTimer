"""
Bunkers module models and schemas
"""

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BunkerStatus(str, Enum):
    """Bunker status enum"""
    ACTIVE = "active"
    EXPIRED = "expired"
    NEAR_EXPIRY = "near_expiry"
    UNKNOWN = "unknown"

class NotificationType(str, Enum):
    """Notification types for bunkers"""
    NEW = "new"
    WARNING_30 = "warning_30"
    WARNING_15 = "warning_15" 
    WARNING_5 = "warning_5"
    EXPIRED = "expired"

class ServerCreate(BaseModel):
    """Server creation schema"""
    name: str
    display_name: str
    description: Optional[str] = None
    max_bunkers: int = 100
    default_notification_channels: Optional[List[str]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Server name cannot be empty')
        if len(v) > 50:
            raise ValueError('Server name too long')
        return v.strip()
    
    @validator('max_bunkers')
    def validate_max_bunkers(cls, v):
        if v <= 0:
            raise ValueError('Max bunkers must be positive')
        if v > 1000:
            raise ValueError('Max bunkers too high (limit 1000)')
        return v

class ServerUpdate(BaseModel):
    """Server update schema"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    max_bunkers: Optional[int] = None
    is_active: Optional[bool] = None
    default_notification_channels: Optional[List[str]] = None
    
    @validator('max_bunkers')
    def validate_max_bunkers(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Max bunkers must be positive')
        if v is not None and v > 1000:
            raise ValueError('Max bunkers too high (limit 1000)')
        return v

class ServerResponse(BaseModel):
    """Server response schema"""
    id: int
    guild_id: str
    name: str
    display_name: str
    description: Optional[str]
    max_bunkers: int
    is_active: bool
    default_notification_channels: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    created_by: str
    total_bunkers: int
    active_bunkers: int

class BunkerSectorCreate(BaseModel):
    """Bunker sector creation schema"""
    sector: str
    name: str
    coordinates: Optional[str] = None
    description: Optional[str] = None
    default_duration_hours: int = 24
    notification_enabled: bool = True
    
    @validator('sector')
    def validate_sector(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Sector cannot be empty')
        if len(v) > 20:
            raise ValueError('Sector too long')
        return v.strip().upper()
    
    @validator('default_duration_hours')
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError('Duration must be positive')
        if v > 168:  # 7 days
            raise ValueError('Duration too long (max 7 days)')
        return v

class BunkerSectorUpdate(BaseModel):
    """Bunker sector update schema"""
    name: Optional[str] = None
    coordinates: Optional[str] = None
    description: Optional[str] = None
    default_duration_hours: Optional[int] = None
    notification_enabled: Optional[bool] = None
    is_active: Optional[bool] = None

class BunkerSectorResponse(BaseModel):
    """Bunker sector response schema"""
    id: int
    guild_id: str
    sector: str
    name: str
    coordinates: Optional[str]
    description: Optional[str]
    default_duration_hours: int
    notification_enabled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    total_registrations: int
    active_registrations: int

class NotificationConfigCreate(BaseModel):
    """Notification configuration creation schema"""
    server_name: str
    bunker_sector: Optional[str] = None
    notification_type: NotificationType
    channel_id: str
    minutes_before: int
    message_template: Optional[str] = None
    role_mention: Optional[str] = None
    enabled: bool = True
    
    @validator('minutes_before')
    def validate_minutes_before(cls, v):
        if v < 0:
            raise ValueError('Minutes before cannot be negative')
        if v > 1440:  # 24 hours
            raise ValueError('Minutes before too high (max 24 hours)')
        return v

class NotificationConfigUpdate(BaseModel):
    """Notification configuration update schema"""
    notification_type: Optional[NotificationType] = None
    channel_id: Optional[str] = None
    minutes_before: Optional[int] = None
    message_template: Optional[str] = None
    role_mention: Optional[str] = None
    enabled: Optional[bool] = None

class NotificationConfigResponse(BaseModel):
    """Notification configuration response schema"""
    id: int
    guild_id: str
    server_name: str
    bunker_sector: Optional[str]
    notification_type: NotificationType
    channel_id: str
    minutes_before: int
    message_template: Optional[str]
    role_mention: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    created_by: str

class BunkerRegistration(BaseModel):
    """Bunker registration response"""
    id: int
    guild_id: str
    sector: str
    name: str
    server_name: str
    registered_time: datetime
    expiry_time: datetime
    registered_by: str
    discord_user_id: str
    last_updated: datetime
    status: BunkerStatus
    time_remaining: Optional[str]
    expired_minutes_ago: Optional[int]

class BunkerRegistrationList(BaseModel):
    """Bunker registrations list"""
    bunkers: List[BunkerRegistration]
    total: int
    active: int
    expired: int
    near_expiry: int
    page: int
    page_size: int

class BunkerStats(BaseModel):
    """Bunker statistics"""
    guild_id: str
    server_name: str
    total_bunkers: int
    active_bunkers: int
    expired_bunkers: int
    near_expiry_bunkers: int
    registrations_today: int
    registrations_this_week: int
    most_active_sector: Optional[str]
    most_active_user: Optional[str]
    average_duration: Optional[float]

class BunkerSystemStats(BaseModel):
    """Global bunker system statistics"""
    total_servers: int
    total_sectors: int
    total_registrations: int
    active_registrations: int
    total_guilds: int
    registrations_today: int
    system_health: str  # healthy, warning, error
    top_servers: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]

class BunkerServerConfig(BaseModel):
    """Bunker server configuration"""
    guild_id: str
    server_name: str
    enabled: bool = True
    max_bunkers_per_user: int = 5
    max_daily_registrations: int = 50
    auto_cleanup_expired: bool = True
    cleanup_after_hours: int = 24
    require_confirmation: bool = False
    allow_anonymous_registration: bool = True
    premium_features_enabled: bool = False

class BunkerAlert(BaseModel):
    """Bunker alert/notification"""
    id: int
    guild_id: str
    server_name: str
    bunker_sector: str
    notification_type: NotificationType
    scheduled_time: datetime
    sent: bool
    sent_time: Optional[datetime]
    channel_id: str
    message_content: str
    error_message: Optional[str]

class BunkerAlertList(BaseModel):
    """Bunker alerts list"""
    alerts: List[BunkerAlert]
    total: int
    pending: int
    sent: int
    failed: int
    page: int
    page_size: int

class BunkerUsageStats(BaseModel):
    """User bunker usage statistics"""
    user_id: str
    username: str
    guild_id: str
    total_registrations: int
    active_bunkers: int
    registrations_today: int
    registrations_this_week: int
    most_used_sector: Optional[str]
    average_duration: Optional[float]
    last_registration: Optional[datetime]
    premium_user: bool

class BunkerManualRegister(BaseModel):
    """Manual bunker registration"""
    server_name: str
    sector: str
    hours: int
    minutes: int = 0
    registered_by: str
    notes: Optional[str] = None
    
    @validator('hours')
    def validate_hours(cls, v):
        if v < 0 or v > 168:  # 7 days max
            raise ValueError('Hours must be between 0 and 168')
        return v
    
    @validator('minutes')
    def validate_minutes(cls, v):
        if v < 0 or v >= 60:
            raise ValueError('Minutes must be between 0 and 59')
        return v

class BunkerBulkAction(BaseModel):
    """Bulk bunker action"""
    action: str  # extend, cancel, cleanup
    bunker_ids: List[int]
    parameters: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    
    @validator('bunker_ids')
    def validate_bunker_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one bunker ID required')
        if len(v) > 100:
            raise ValueError('Too many bunkers (max 100)')
        return v

class BunkerExportRequest(BaseModel):
    """Bunker data export request"""
    format: str  # json, csv, xlsx
    date_range: Optional[Dict[str, str]] = None
    server_filter: Optional[str] = None
    status_filter: Optional[BunkerStatus] = None
    include_expired: bool = False
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['json', 'csv', 'xlsx']:
            raise ValueError('Invalid format')
        return v