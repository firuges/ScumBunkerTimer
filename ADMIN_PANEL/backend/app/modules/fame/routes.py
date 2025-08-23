"""
Fame Points module routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import json
from datetime import datetime

from app.core.database import db_manager
from app.auth.routes import get_current_user, require_permission
from app.auth.models import UserProfile
from .models import (
    FameRewardCreate, FameRewardUpdate, FameRewardResponse, FameRewardList,
    FameUserStats, FameLeaderboard, FameTransaction, FameTransactionList,
    FameAdjustment, FameBulkAdjustment, FameSystemConfig, FameSystemStats,
    FameRewardPurchase, FameRewardPurchaseResponse, RewardType
)

router = APIRouter()

@router.get("/rewards", response_model=FameRewardList)
async def get_fame_rewards(
    guild_id: str = Query(..., description="Guild ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    current_user: UserProfile = Depends(require_permission("fame_points"))
):
    """Get fame rewards for a guild"""
    # Check if user has access to this guild
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Build query with pagination
    where_clause = "WHERE guild_id = ?"
    params = [guild_id]
    
    if active_only:
        where_clause += " AND is_active = 1"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as count FROM admin_fame_rewards {where_clause}"
    count_result = await db_manager.execute_query(count_query, tuple(params))
    total = count_result[0]['count']
    
    # Get rewards with pagination
    offset = (page - 1) * page_size
    query = f"""
        SELECT * FROM admin_fame_rewards 
        {where_clause}
        ORDER BY fame_cost ASC, reward_name ASC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    
    rewards_data = await db_manager.execute_query(query, tuple(params))
    
    rewards = []
    for reward in rewards_data:
        rewards.append(FameRewardResponse(
            id=reward['id'],
            guild_id=reward['guild_id'],
            reward_name=reward['reward_name'],
            fame_cost=reward['fame_cost'],
            reward_type=RewardType(reward['reward_type']),
            reward_value=json.loads(reward['reward_value']),
            description=reward['description'],
            is_active=bool(reward['is_active']),
            max_purchases=reward['max_purchases'],
            cooldown_hours=reward['cooldown_hours'],
            required_role=reward['required_role'],
            created_at=datetime.fromisoformat(reward['created_at']),
            updated_at=datetime.fromisoformat(reward['updated_at']),
            created_by=reward['created_by']
        ))
    
    return FameRewardList(
        rewards=rewards,
        total=total,
        page=page,
        page_size=page_size
    )

@router.post("/rewards", response_model=FameRewardResponse)
async def create_fame_reward(
    guild_id: str = Query(..., description="Guild ID"),
    reward_data: FameRewardCreate = ...,
    current_user: UserProfile = Depends(require_permission("fame_points"))
):
    """Create a new fame reward"""
    # Check access
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Check for duplicate name in guild
    check_query = "SELECT id FROM admin_fame_rewards WHERE guild_id = ? AND reward_name = ?"
    existing = await db_manager.execute_query(check_query, (guild_id, reward_data.reward_name))
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reward name already exists in this guild"
        )
    
    # Insert new reward
    insert_query = """
        INSERT INTO admin_fame_rewards 
        (guild_id, reward_name, fame_cost, reward_type, reward_value, description,
         max_purchases, cooldown_hours, required_role, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    result = await db_manager.execute_command(
        insert_query,
        (
            guild_id,
            reward_data.reward_name,
            reward_data.fame_cost,
            reward_data.reward_type.value,
            json.dumps(reward_data.reward_value),
            reward_data.description,
            reward_data.max_purchases,
            reward_data.cooldown_hours,
            reward_data.required_role,
            current_user.id
        )
    )
    
    # Get the created reward
    reward_query = "SELECT * FROM admin_fame_rewards WHERE guild_id = ? AND reward_name = ?"
    created_reward = await db_manager.execute_query(
        reward_query, 
        (guild_id, reward_data.reward_name)
    )
    
    reward = created_reward[0]
    return FameRewardResponse(
        id=reward['id'],
        guild_id=reward['guild_id'],
        reward_name=reward['reward_name'],
        fame_cost=reward['fame_cost'],
        reward_type=RewardType(reward['reward_type']),
        reward_value=json.loads(reward['reward_value']),
        description=reward['description'],
        is_active=bool(reward['is_active']),
        max_purchases=reward['max_purchases'],
        cooldown_hours=reward['cooldown_hours'],
        required_role=reward['required_role'],
        created_at=datetime.fromisoformat(reward['created_at']),
        updated_at=datetime.fromisoformat(reward['updated_at']),
        created_by=reward['created_by']
    )

@router.put("/rewards/{reward_id}", response_model=FameRewardResponse)
async def update_fame_reward(
    reward_id: int,
    guild_id: str = Query(..., description="Guild ID"),
    reward_data: FameRewardUpdate = ...,
    current_user: UserProfile = Depends(require_permission("fame_points"))
):
    """Update a fame reward"""
    # Check access
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Check if reward exists
    check_query = "SELECT * FROM admin_fame_rewards WHERE id = ? AND guild_id = ?"
    existing = await db_manager.execute_query(check_query, (reward_id, guild_id))
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found"
        )
    
    # Build update query
    update_fields = []
    params = []
    
    if reward_data.reward_name is not None:
        update_fields.append("reward_name = ?")
        params.append(reward_data.reward_name)
    
    if reward_data.fame_cost is not None:
        update_fields.append("fame_cost = ?")
        params.append(reward_data.fame_cost)
    
    if reward_data.reward_type is not None:
        update_fields.append("reward_type = ?")
        params.append(reward_data.reward_type.value)
    
    if reward_data.reward_value is not None:
        update_fields.append("reward_value = ?")
        params.append(json.dumps(reward_data.reward_value))
    
    if reward_data.description is not None:
        update_fields.append("description = ?")
        params.append(reward_data.description)
    
    if reward_data.is_active is not None:
        update_fields.append("is_active = ?")
        params.append(int(reward_data.is_active))
    
    if reward_data.max_purchases is not None:
        update_fields.append("max_purchases = ?")
        params.append(reward_data.max_purchases)
    
    if reward_data.cooldown_hours is not None:
        update_fields.append("cooldown_hours = ?")
        params.append(reward_data.cooldown_hours)
    
    if reward_data.required_role is not None:
        update_fields.append("required_role = ?")
        params.append(reward_data.required_role)
    
    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([reward_id, guild_id])
        
        update_query = f"""
            UPDATE admin_fame_rewards 
            SET {', '.join(update_fields)} 
            WHERE id = ? AND guild_id = ?
        """
        
        await db_manager.execute_command(update_query, tuple(params))
    
    # Return updated reward
    updated_reward = await db_manager.execute_query(check_query, (reward_id, guild_id))
    reward = updated_reward[0]
    
    return FameRewardResponse(
        id=reward['id'],
        guild_id=reward['guild_id'],
        reward_name=reward['reward_name'],
        fame_cost=reward['fame_cost'],
        reward_type=RewardType(reward['reward_type']),
        reward_value=json.loads(reward['reward_value']),
        description=reward['description'],
        is_active=bool(reward['is_active']),
        max_purchases=reward['max_purchases'],
        cooldown_hours=reward['cooldown_hours'],
        required_role=reward['required_role'],
        created_at=datetime.fromisoformat(reward['created_at']),
        updated_at=datetime.fromisoformat(reward['updated_at']),
        created_by=reward['created_by']
    )

@router.delete("/rewards/{reward_id}")
async def delete_fame_reward(
    reward_id: int,
    guild_id: str = Query(..., description="Guild ID"),
    current_user: UserProfile = Depends(require_permission("fame_points"))
):
    """Delete a fame reward"""
    # Check access
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Check if reward exists
    check_query = "SELECT id FROM admin_fame_rewards WHERE id = ? AND guild_id = ?"
    existing = await db_manager.execute_query(check_query, (reward_id, guild_id))
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found"
        )
    
    # Delete reward
    delete_query = "DELETE FROM admin_fame_rewards WHERE id = ? AND guild_id = ?"
    await db_manager.execute_command(delete_query, (reward_id, guild_id))
    
    return {"message": "Reward deleted successfully"}

@router.get("/leaderboard", response_model=FameLeaderboard)
async def get_fame_leaderboard(
    guild_id: str = Query(..., description="Guild ID"),
    limit: int = Query(50, ge=1, le=100),
    current_user: UserProfile = Depends(require_permission("fame_points"))
):
    """Get fame points leaderboard"""
    # Check access
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Get leaderboard from bot database
    query = """
        SELECT discord_id, username, 
               CAST(fame_points AS INTEGER) as current_fame,
               CAST(total_earned_fame AS INTEGER) as total_earned,
               CAST(total_spent_fame AS INTEGER) as total_spent,
               ROW_NUMBER() OVER (ORDER BY CAST(fame_points AS INTEGER) DESC) as rank_position,
               last_fame_update
        FROM users 
        WHERE guild_id = ? AND CAST(fame_points AS INTEGER) > 0
        ORDER BY CAST(fame_points AS INTEGER) DESC
        LIMIT ?
    """
    
    result = await db_manager.execute_query(query, (guild_id, limit))
    
    users = []
    for row in result:
        users.append(FameUserStats(
            user_id=row['discord_id'],
            username=row['username'] or f"User#{row['discord_id'][-4:]}",
            current_fame=row['current_fame'],
            total_earned=row['total_earned'] or 0,
            total_spent=row['total_spent'] or 0,
            rank_position=row['rank_position'],
            rewards_purchased=0,  # Would need additional query
            last_activity=datetime.fromisoformat(row['last_fame_update']) if row['last_fame_update'] else None
        ))
    
    # Get total users count
    count_query = "SELECT COUNT(*) as count FROM users WHERE guild_id = ? AND CAST(fame_points AS INTEGER) > 0"
    count_result = await db_manager.execute_query(count_query, (guild_id,))
    total_users = count_result[0]['count']
    
    return FameLeaderboard(
        users=users,
        total_users=total_users,
        updated_at=datetime.utcnow()
    )

@router.post("/adjust")
async def adjust_fame_points(
    guild_id: str = Query(..., description="Guild ID"),
    adjustment: FameAdjustment = ...,
    current_user: UserProfile = Depends(require_permission("fame_points"))
):
    """Adjust user's fame points"""
    # Check access
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Check if user exists
    user_query = "SELECT fame_points FROM users WHERE discord_id = ? AND guild_id = ?"
    user_result = await db_manager.execute_query(user_query, (adjustment.user_id, guild_id))
    
    if not user_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this guild"
        )
    
    current_fame = int(user_result[0]['fame_points'])
    new_fame = max(0, current_fame + adjustment.amount)  # Don't allow negative fame
    
    # Update user's fame
    update_query = """
        UPDATE users 
        SET fame_points = ?, 
            total_earned_fame = CASE 
                WHEN ? > 0 THEN COALESCE(CAST(total_earned_fame AS INTEGER), 0) + ?
                ELSE COALESCE(CAST(total_earned_fame AS INTEGER), 0)
            END,
            total_spent_fame = CASE 
                WHEN ? < 0 THEN COALESCE(CAST(total_spent_fame AS INTEGER), 0) + ABS(?)
                ELSE COALESCE(CAST(total_spent_fame AS INTEGER), 0)
            END,
            last_fame_update = CURRENT_TIMESTAMP
        WHERE discord_id = ? AND guild_id = ?
    """
    
    await db_manager.execute_command(
        update_query, 
        (new_fame, adjustment.amount, adjustment.amount, 
         adjustment.amount, adjustment.amount, 
         adjustment.user_id, guild_id)
    )
    
    return {
        "message": "Fame points adjusted successfully",
        "user_id": adjustment.user_id,
        "old_fame": current_fame,
        "new_fame": new_fame,
        "adjustment": adjustment.amount,
        "reason": adjustment.reason
    }