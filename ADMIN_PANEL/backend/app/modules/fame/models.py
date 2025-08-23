"""
Fame Points module models and schemas
"""

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RewardType(str, Enum):
    """Reward types enum"""
    ROLE = "role"
    ITEM = "item"
    MONEY = "money"
    CUSTOM = "custom"

class FameRewardCreate(BaseModel):
    """Fame reward creation schema"""
    reward_name: str
    fame_cost: int
    reward_type: RewardType
    reward_value: Dict[str, Any]
    description: Optional[str] = None
    max_purchases: Optional[int] = None
    cooldown_hours: int = 0
    required_role: Optional[str] = None
    
    @validator('fame_cost')
    def validate_fame_cost(cls, v):
        if v <= 0:
            raise ValueError('Fame cost must be positive')
        return v
    
    @validator('reward_name')
    def validate_reward_name(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Reward name cannot be empty')
        if len(v) > 100:
            raise ValueError('Reward name too long')
        return v.strip()

class FameRewardUpdate(BaseModel):
    """Fame reward update schema"""
    reward_name: Optional[str] = None
    fame_cost: Optional[int] = None
    reward_type: Optional[RewardType] = None
    reward_value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    max_purchases: Optional[int] = None
    cooldown_hours: Optional[int] = None
    required_role: Optional[str] = None
    
    @validator('fame_cost')
    def validate_fame_cost(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Fame cost must be positive')
        return v

class FameRewardResponse(BaseModel):
    """Fame reward response schema"""
    id: int
    guild_id: str
    reward_name: str
    fame_cost: int
    reward_type: RewardType
    reward_value: Dict[str, Any]
    description: Optional[str]
    is_active: bool
    max_purchases: Optional[int]
    cooldown_hours: int
    required_role: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: str

class FameRewardList(BaseModel):
    """Fame rewards list response"""
    rewards: List[FameRewardResponse]
    total: int
    page: int
    page_size: int

class FameUserStats(BaseModel):
    """Fame user statistics"""
    user_id: str
    username: str
    current_fame: int
    total_earned: int
    total_spent: int
    rank_position: int
    rewards_purchased: int
    last_activity: Optional[datetime]

class FameLeaderboard(BaseModel):
    """Fame points leaderboard"""
    users: List[FameUserStats]
    total_users: int
    updated_at: datetime

class FameTransaction(BaseModel):
    """Fame transaction record"""
    id: int
    user_id: str
    username: str
    transaction_type: str  # earned, spent, adjusted
    amount: int
    reason: str
    related_reward_id: Optional[int]
    timestamp: datetime
    admin_id: Optional[str]

class FameTransactionList(BaseModel):
    """Fame transactions list"""
    transactions: List[FameTransaction]
    total: int
    page: int
    page_size: int

class FameAdjustment(BaseModel):
    """Fame points adjustment"""
    user_id: str
    amount: int  # Can be negative
    reason: str
    
    @validator('reason')
    def validate_reason(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Reason cannot be empty')
        return v.strip()

class FameBulkAdjustment(BaseModel):
    """Bulk fame points adjustment"""
    adjustments: List[FameAdjustment]
    
    @validator('adjustments')
    def validate_adjustments(cls, v):
        if len(v) == 0:
            raise ValueError('At least one adjustment required')
        if len(v) > 50:
            raise ValueError('Too many adjustments at once (max 50)')
        return v

class FameSystemConfig(BaseModel):
    """Fame system configuration"""
    guild_id: str
    enabled: bool = True
    daily_base_fame: int = 10
    voice_fame_per_hour: int = 5
    message_fame_points: int = 1
    reaction_fame_points: int = 2
    max_daily_fame: int = 100
    fame_decay_enabled: bool = False
    fame_decay_rate: float = 0.01  # 1% per day
    leaderboard_enabled: bool = True
    reward_announcements: bool = True

class FameSystemStats(BaseModel):
    """Fame system statistics"""
    guild_id: str
    total_users: int
    total_fame_distributed: int
    total_rewards_purchased: int
    active_rewards: int
    top_earner: Optional[Dict[str, Any]]
    recent_transactions: int
    system_health: str  # healthy, warning, error

class FameRewardPurchase(BaseModel):
    """Fame reward purchase request"""
    reward_id: int
    user_id: str
    
class FameRewardPurchaseResponse(BaseModel):
    """Fame reward purchase response"""
    success: bool
    message: str
    new_fame_balance: Optional[int]
    transaction_id: Optional[int]