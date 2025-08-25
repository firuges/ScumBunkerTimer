from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BankingConfigBase(BaseModel):
    bank_channel_id: Optional[str] = None
    welcome_bonus: int = Field(default=7500, ge=0)
    daily_bonus: int = Field(default=500, ge=0)
    min_balance: int = Field(default=0)
    max_balance: int = Field(default=1000000, ge=0)
    transfer_fee_percent: float = Field(default=2.5, ge=0, le=100)
    min_transfer_amount: int = Field(default=100, ge=0)
    max_transfer_amount: int = Field(default=50000, ge=0)
    max_daily_transfers: int = Field(default=10, ge=1)
    overdraft_enabled: bool = Field(default=False)
    overdraft_limit: int = Field(default=0, ge=0)
    interest_rate: float = Field(default=0.1, ge=0, le=100)
    bank_hours_start: str = Field(default="08:00")
    bank_hours_end: str = Field(default="20:00")
    weekend_enabled: bool = Field(default=True)

class BankingConfigCreate(BankingConfigBase):
    guild_id: str

class BankingConfigUpdate(BankingConfigBase):
    pass

class BankingConfig(BankingConfigBase):
    id: int
    guild_id: str
    created_at: datetime
    updated_at: datetime
    updated_by: int

    class Config:
        from_attributes = True

class AccountTypeBase(BaseModel):
    account_type_name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    min_balance: int = Field(default=0)
    max_balance: int = Field(default=100000, ge=0)
    daily_limit: int = Field(default=10000, ge=0)
    transfer_fee_percent: float = Field(default=2.5, ge=0, le=100)
    monthly_fee: int = Field(default=0, ge=0)
    interest_rate: float = Field(default=0.1, ge=0, le=100)
    overdraft_limit: int = Field(default=0, ge=0)
    required_role: Optional[str] = None
    is_active: bool = Field(default=True)

class AccountTypeCreate(AccountTypeBase):
    guild_id: str

class AccountTypeUpdate(AccountTypeBase):
    pass

class AccountType(AccountTypeBase):
    id: int
    guild_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class BankingFeeBase(BaseModel):
    fee_type: str = Field(...)
    fee_name: str = Field(..., min_length=1, max_length=100)
    fee_method: str = Field(default="percentage")
    fee_value: float = Field(..., ge=0)
    min_amount: int = Field(default=0, ge=0)
    max_amount: Optional[int] = Field(default=None, ge=0)
    applies_to: str = Field(default="all")
    description: Optional[str] = None
    is_active: bool = Field(default=True)

class BankingFeeCreate(BankingFeeBase):
    guild_id: str

class BankingFeeUpdate(BankingFeeBase):
    pass

class BankingFee(BankingFeeBase):
    id: int
    guild_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class BankingChannelBase(BaseModel):
    channel_type: str = Field(...)
    channel_id: str = Field(..., min_length=1)
    channel_name: Optional[str] = None
    auto_delete_messages: bool = Field(default=False)
    delete_after_minutes: int = Field(default=60, ge=1)
    embed_color: str = Field(default="#00FF00")
    ping_role: Optional[str] = None
    is_active: bool = Field(default=True)

class BankingChannelCreate(BankingChannelBase):
    guild_id: str

class BankingChannelUpdate(BankingChannelBase):
    pass

class BankingChannel(BankingChannelBase):
    id: int
    guild_id: str
    created_at: datetime

    class Config:
        from_attributes = True