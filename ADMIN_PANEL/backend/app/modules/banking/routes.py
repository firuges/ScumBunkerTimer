from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import sqlite3
from .models import (
    BankingConfig, BankingConfigCreate, BankingConfigUpdate,
    AccountType, AccountTypeCreate, AccountTypeUpdate,
    BankingFee, BankingFeeCreate, BankingFeeUpdate,
    BankingChannel, BankingChannelCreate, BankingChannelUpdate
)

router = APIRouter()

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect("../../scum_main.db")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Banking Configuration Endpoints
@router.get("/config", response_model=BankingConfig)
async def get_banking_config(guild_id: str = "123456789"):
    """Get banking configuration for a guild"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, guild_id, bank_channel_id, welcome_bonus, daily_bonus,
                   min_balance, max_balance, transfer_fee_percent, min_transfer_amount,
                   max_transfer_amount, max_daily_transfers, overdraft_enabled,
                   overdraft_limit, interest_rate, bank_hours_start, bank_hours_end,
                   weekend_enabled, created_at, updated_at, updated_by
            FROM admin_banking_config 
            WHERE guild_id = ?
        """, (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Banking configuration not found")
        
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching banking config: {str(e)}")

@router.post("/config", response_model=BankingConfig)
async def create_banking_config(config: BankingConfigCreate):
    """Create or update banking configuration"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO admin_banking_config 
            (guild_id, bank_channel_id, welcome_bonus, daily_bonus, min_balance,
             max_balance, transfer_fee_percent, min_transfer_amount, max_transfer_amount,
             max_daily_transfers, overdraft_enabled, overdraft_limit, interest_rate,
             bank_hours_start, bank_hours_end, weekend_enabled, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            config.guild_id, config.bank_channel_id, config.welcome_bonus,
            config.daily_bonus, config.min_balance, config.max_balance,
            config.transfer_fee_percent, config.min_transfer_amount,
            config.max_transfer_amount, config.max_daily_transfers,
            config.overdraft_enabled, config.overdraft_limit, config.interest_rate,
            config.bank_hours_start, config.bank_hours_end, config.weekend_enabled
        ))
        
        conn.commit()
        conn.close()
        
        return await get_banking_config(config.guild_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating banking config: {str(e)}")

@router.put("/config", response_model=BankingConfig)
async def update_banking_config(config: BankingConfigUpdate, guild_id: str = "123456789"):
    """Update banking configuration"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE admin_banking_config SET
                bank_channel_id = ?, welcome_bonus = ?, daily_bonus = ?,
                min_balance = ?, max_balance = ?, transfer_fee_percent = ?,
                min_transfer_amount = ?, max_transfer_amount = ?, max_daily_transfers = ?,
                overdraft_enabled = ?, overdraft_limit = ?, interest_rate = ?,
                bank_hours_start = ?, bank_hours_end = ?, weekend_enabled = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
        """, (
            config.bank_channel_id, config.welcome_bonus, config.daily_bonus,
            config.min_balance, config.max_balance, config.transfer_fee_percent,
            config.min_transfer_amount, config.max_transfer_amount,
            config.max_daily_transfers, config.overdraft_enabled,
            config.overdraft_limit, config.interest_rate, config.bank_hours_start,
            config.bank_hours_end, config.weekend_enabled, guild_id
        ))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Banking configuration not found")
        
        conn.commit()
        conn.close()
        
        return await get_banking_config(guild_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating banking config: {str(e)}")

# Account Types Endpoints
@router.get("/account-types", response_model=List[AccountType])
async def get_account_types(guild_id: str = "123456789"):
    """Get all account types for a guild"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, guild_id, account_type_name, display_name, description,
                   min_balance, max_balance, daily_limit, transfer_fee_percent,
                   monthly_fee, interest_rate, overdraft_limit, required_role,
                   is_active, created_at
            FROM admin_banking_account_types 
            WHERE guild_id = ? 
            ORDER BY account_type_name
        """, (guild_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching account types: {str(e)}")

@router.post("/account-types", response_model=AccountType)
async def create_account_type(account_type: AccountTypeCreate):
    """Create new account type"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO admin_banking_account_types 
            (guild_id, account_type_name, display_name, description, min_balance,
             max_balance, daily_limit, transfer_fee_percent, monthly_fee,
             interest_rate, overdraft_limit, required_role, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account_type.guild_id, account_type.account_type_name,
            account_type.display_name, account_type.description,
            account_type.min_balance, account_type.max_balance,
            account_type.daily_limit, account_type.transfer_fee_percent,
            account_type.monthly_fee, account_type.interest_rate,
            account_type.overdraft_limit, account_type.required_role,
            account_type.is_active
        ))
        
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        cursor.execute("""
            SELECT id, guild_id, account_type_name, display_name, description,
                   min_balance, max_balance, daily_limit, transfer_fee_percent,
                   monthly_fee, interest_rate, overdraft_limit, required_role,
                   is_active, created_at
            FROM admin_banking_account_types 
            WHERE id = ?
        """, (account_id,))
        
        result = cursor.fetchone()
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating account type: {str(e)}")

# Banking Fees Endpoints
@router.get("/fees", response_model=List[BankingFee])
async def get_banking_fees(guild_id: str = "123456789"):
    """Get all banking fees for a guild"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, guild_id, fee_type, fee_name, fee_method, fee_value,
                   min_amount, max_amount, applies_to, description, is_active, created_at
            FROM admin_banking_fees 
            WHERE guild_id = ? 
            ORDER BY fee_type, fee_name
        """, (guild_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching banking fees: {str(e)}")

# Banking Channels Endpoints
@router.get("/channels", response_model=List[BankingChannel])
async def get_banking_channels(guild_id: str = "123456789"):
    """Get all banking channels for a guild"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, guild_id, channel_type, channel_id, channel_name,
                   auto_delete_messages, delete_after_minutes, embed_color,
                   ping_role, is_active, created_at
            FROM admin_banking_channels 
            WHERE guild_id = ? 
            ORDER BY channel_type
        """, (guild_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching banking channels: {str(e)}")

@router.post("/channels", response_model=BankingChannel)
async def create_banking_channel(channel: BankingChannelCreate):
    """Create new banking channel"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO admin_banking_channels 
            (guild_id, channel_type, channel_id, channel_name, auto_delete_messages,
             delete_after_minutes, embed_color, ping_role, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            channel.guild_id, channel.channel_type, channel.channel_id,
            channel.channel_name, channel.auto_delete_messages,
            channel.delete_after_minutes, channel.embed_color,
            channel.ping_role, channel.is_active
        ))
        
        conn.commit()
        channel_id = cursor.lastrowid
        conn.close()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, guild_id, channel_type, channel_id, channel_name,
                   auto_delete_messages, delete_after_minutes, embed_color,
                   ping_role, is_active, created_at
            FROM admin_banking_channels 
            WHERE guild_id = ? AND channel_type = ?
        """, (channel.guild_id, channel.channel_type))
        
        result = cursor.fetchone()
        conn.close()
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating banking channel: {str(e)}")