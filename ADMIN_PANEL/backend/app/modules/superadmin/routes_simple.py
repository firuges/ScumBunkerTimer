"""
Super Admin Routes - Panel de administración global simplificado
Para el dueño del bot con gestión cross-server
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import sqlite3
import json
import os
from datetime import datetime, timedelta
from .models import (
    GlobalDashboard, GlobalAnalytics, DiscordServerInfo, 
    ServerManagement, SubscriptionManagement, SubscriptionUpdate,
    ServerUsageStats, SystemHealthCheck, AdminAction,
    SubscriptionPlan, ServerStatus, CreateServerOverride, ServerActionBulk
)

router = APIRouter()

# Database path - same as other modules
def get_db_path():
    return os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "scum_main.db")

# Owner authentication check (simplified - in production use JWT)
def verify_owner_access(user_id: str = "OWNER_ID_PLACEHOLDER"):
    """Verify that the user is the bot owner - simplified version"""
    # In production, this would check JWT token and verify Discord OAuth2
    # For now, we'll use a placeholder system
    return user_id == "OWNER_ID_PLACEHOLDER" or user_id == "123456789"

@router.get("/dashboard", response_model=GlobalDashboard)
async def get_global_dashboard(
    owner_id: str = Query("OWNER_ID_PLACEHOLDER", description="Bot owner Discord ID")
):
    """Dashboard global consolidado para el dueño del bot"""
    
    if not verify_owner_access(owner_id):
        raise HTTPException(status_code=403, detail="Access denied - Owner only")
    
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Global Analytics
        analytics = await get_global_analytics(cursor)
        
        # Recent Admin Actions (mock data for now)
        recent_actions = [
            AdminAction(
                id=1,
                admin_id=owner_id,
                admin_username="BotOwner",
                action_type="subscription_upgrade",
                target_guild_id="123456789",
                details={"from": "free", "to": "premium", "duration": 1},
                timestamp=datetime.now()
            ),
            AdminAction(
                id=2,
                admin_id=owner_id,
                admin_username="BotOwner", 
                action_type="server_configuration",
                target_guild_id="987654321",
                details={"module": "banking", "action": "config_update"},
                timestamp=datetime.now() - timedelta(hours=2)
            )
        ]
        
        # System Health
        system_health = [
            SystemHealthCheck(
                service_name="Database",
                status="healthy",
                response_time=12.5,
                uptime_percentage=99.9,
                last_check=datetime.now(),
                error_count=0
            ),
            SystemHealthCheck(
                service_name="API Backend",
                status="healthy", 
                response_time=45.2,
                uptime_percentage=99.7,
                last_check=datetime.now(),
                error_count=2
            ),
            SystemHealthCheck(
                service_name="Discord Bot",
                status="healthy",
                response_time=156.8,
                uptime_percentage=99.5,
                last_check=datetime.now(),
                error_count=5
            )
        ]
        
        # Top Servers Usage
        top_servers = await get_top_servers_usage(cursor, limit=5)
        
        # System Alerts
        alerts = [
            "Server 'TestGuild' subscription expires in 3 days",
            "High API usage detected on 2 servers",
            "Database backup completed successfully"
        ]
        
        conn.close()
        
        return GlobalDashboard(
            analytics=analytics,
            recent_actions=recent_actions,
            system_health=system_health,
            top_servers=top_servers,
            alerts=alerts
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading global dashboard: {str(e)}")


async def get_global_analytics(cursor) -> GlobalAnalytics:
    """Generar analytics globales consolidadas"""
    
    # Count total servers with bot configurations
    cursor.execute("""
        SELECT COUNT(DISTINCT guild_id) as total_servers 
        FROM (
            SELECT guild_id FROM admin_fame_rewards
            UNION
            SELECT guild_id FROM admin_banking_config  
            UNION
            SELECT guild_id FROM admin_taxi_config
            UNION 
            SELECT guild_id FROM admin_mechanic_config
            UNION
            SELECT guild_id FROM admin_bunker_config
        )
    """)
    total_servers = cursor.fetchone()[0] or 0
    
    # Active servers (servers with recent activity - simplified)
    active_servers = max(1, total_servers)  # Simplified: assume all are active
    
    # Premium/VIP counts (mock data for now)
    premium_servers = max(1, total_servers // 3)
    vip_servers = max(1, total_servers // 5)
    
    # Estimate total users (mock calculation)
    total_users = total_servers * 150  # Average 150 users per server
    daily_active_users = total_users // 5  # 20% daily activity rate
    
    # Revenue calculation (mock)
    monthly_revenue = premium_servers * 9.99 + vip_servers * 19.99
    
    # Top features based on table record counts
    cursor.execute("SELECT COUNT(*) FROM admin_fame_rewards")
    fame_usage = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM admin_banking_config")  
    banking_usage = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM admin_taxi_config")
    taxi_usage = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM admin_mechanic_config") 
    mechanic_usage = cursor.fetchone()[0] or 0
    
    top_features = [
        {"feature": "Fame Points", "usage": fame_usage * 100, "growth": "+15%"},
        {"feature": "Banking System", "usage": banking_usage * 85, "growth": "+23%"},
        {"feature": "Taxi Service", "usage": taxi_usage * 65, "growth": "+8%"},
        {"feature": "Mechanic Services", "usage": mechanic_usage * 45, "growth": "+31%"}
    ]
    
    # Growth metrics
    growth_metrics = {
        "new_servers_today": 2,
        "new_servers_week": 12, 
        "new_servers_month": 47,
        "churned_servers_month": 5
    }
    
    # System health summary
    system_health = {
        "overall_uptime": 99.7,
        "api_response_time": 67.3,
        "database_performance": 95.8,
        "error_rate": 0.3
    }
    
    return GlobalAnalytics(
        total_servers=total_servers,
        active_servers=active_servers,
        premium_servers=premium_servers,
        vip_servers=vip_servers,
        total_users=total_users,
        daily_active_users=daily_active_users,
        monthly_revenue=monthly_revenue,
        top_features=top_features,
        growth_metrics=growth_metrics,
        system_health=system_health
    )


async def get_top_servers_usage(cursor, limit: int = 10) -> List[ServerUsageStats]:
    """Obtener servidores con mayor uso del bot"""
    
    # Get unique guild_ids from all modules
    cursor.execute("""
        SELECT DISTINCT guild_id FROM (
            SELECT guild_id FROM admin_fame_rewards
            UNION
            SELECT guild_id FROM admin_banking_config
            UNION 
            SELECT guild_id FROM admin_taxi_config
            UNION
            SELECT guild_id FROM admin_mechanic_config
            UNION
            SELECT guild_id FROM admin_bunker_config
        ) LIMIT ?
    """, (limit,))
    
    guild_rows = cursor.fetchall()
    top_servers = []
    
    for idx, row in enumerate(guild_rows):
        guild_id = row[0]
        
        # Generate mock usage statistics
        top_servers.append(ServerUsageStats(
            guild_id=guild_id,
            guild_name=f"Server_{guild_id[-4:]}" if guild_id != "123456789" else "Main Test Server",
            commands_used_today=150 - (idx * 20),
            commands_used_month=4500 - (idx * 500),
            active_users_today=45 - (idx * 5),
            active_users_month=1200 - (idx * 100),
            most_used_features=["Fame Points", "Banking", "Taxi"][:3-idx] if idx < 3 else ["Banking"],
            revenue_generated=99.99 if idx < 2 else 0.0,
            last_activity=datetime.now() - timedelta(hours=idx)
        ))
    
    return top_servers


@router.get("/servers", response_model=ServerManagement)
async def get_all_servers(
    owner_id: str = Query("OWNER_ID_PLACEHOLDER"),
    status_filter: Optional[str] = Query(None),
    plan_filter: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """Lista completa de servidores Discord que usan el bot"""
    
    if not verify_owner_access(owner_id):
        raise HTTPException(status_code=403, detail="Access denied - Owner only")
    
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all unique guild_ids from bot configuration tables
        cursor.execute("""
            SELECT DISTINCT guild_id FROM (
                SELECT guild_id FROM admin_fame_rewards
                UNION
                SELECT guild_id FROM admin_banking_config
                UNION 
                SELECT guild_id FROM admin_taxi_config
                UNION
                SELECT guild_id FROM admin_mechanic_config
                UNION
                SELECT guild_id FROM admin_bunker_config
            ) LIMIT ?
        """, (limit,))
        
        guild_rows = cursor.fetchall()
        servers = []
        
        for idx, row in enumerate(guild_rows):
            guild_id = row[0]
            
            # Generate server info (mock data - in production would fetch from Discord API)
            servers.append(DiscordServerInfo(
                guild_id=guild_id,
                guild_name=f"Server_{guild_id[-4:]}" if guild_id != "123456789" else "Main Test Server",
                owner_id=f"owner_{idx + 1}",
                owner_username=f"ServerOwner{idx + 1}",
                member_count=250 + (idx * 50),
                created_at=datetime.now() - timedelta(days=30 * (idx + 1)),
                subscription_plan=SubscriptionPlan.PREMIUM if idx < 2 else SubscriptionPlan.FREE,
                status=ServerStatus.ACTIVE,
                last_activity=datetime.now() - timedelta(hours=idx),
                features_enabled=["fame", "banking", "taxi", "mechanic", "bunkers"][:5-idx],
                monthly_usage={
                    "commands": 4500 - (idx * 500),
                    "api_calls": 12000 - (idx * 1000), 
                    "active_users": 120 - (idx * 10)
                }
            ))
        
        # Subscription summary
        subscription_summary = {
            "free": len([s for s in servers if s.subscription_plan == SubscriptionPlan.FREE]),
            "premium": len([s for s in servers if s.subscription_plan == SubscriptionPlan.PREMIUM]),
            "vip": len([s for s in servers if s.subscription_plan == SubscriptionPlan.VIP])
        }
        
        conn.close()
        
        return ServerManagement(
            servers=servers,
            total_count=len(servers),
            filter_applied=status_filter or plan_filter,
            subscription_summary=subscription_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading servers: {str(e)}")


@router.put("/servers/{guild_id}/subscription")
async def update_server_subscription(
    guild_id: str,
    subscription_update: SubscriptionUpdate,
    owner_id: str = Query("OWNER_ID_PLACEHOLDER")
):
    """Actualizar suscripción de un servidor específico"""
    
    if not verify_owner_access(owner_id):
        raise HTTPException(status_code=403, detail="Access denied - Owner only")
    
    try:
        # In production, this would update subscription tables
        # For now, return success response with mock data
        
        return {
            "success": True,
            "guild_id": guild_id,
            "old_plan": "free",
            "new_plan": subscription_update.new_plan,
            "effective_date": datetime.now().isoformat(),
            "expires_date": (datetime.now() + timedelta(days=30 * subscription_update.duration_months)).isoformat(),
            "updated_by": owner_id,
            "reason": subscription_update.reason
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating subscription: {str(e)}")


@router.post("/servers/bulk-action")
async def bulk_server_action(
    action_request: ServerActionBulk,
    owner_id: str = Query("OWNER_ID_PLACEHOLDER")
):
    """Ejecutar acciones en lote sobre múltiples servidores"""
    
    if not verify_owner_access(owner_id):
        raise HTTPException(status_code=403, detail="Access denied - Owner only")
    
    try:
        results = []
        
        for guild_id in action_request.guild_ids:
            # Mock processing each server
            results.append({
                "guild_id": guild_id,
                "action": action_request.action,
                "status": "success",
                "message": f"Successfully {action_request.action}d server {guild_id}",
                "processed_at": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "processed_count": len(results),
            "results": results,
            "action": action_request.action,
            "reason": action_request.reason,
            "processed_by": owner_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing bulk action: {str(e)}")


@router.get("/subscriptions", response_model=SubscriptionManagement)
async def get_subscription_management(
    owner_id: str = Query("OWNER_ID_PLACEHOLDER")
):
    """Panel de gestión de suscripciones y revenue"""
    
    if not verify_owner_access(owner_id):
        raise HTTPException(status_code=403, detail="Access denied - Owner only")
    
    try:
        # Mock subscription management data
        from .models import SubscriptionHistory
        
        active_subscriptions = [
            SubscriptionHistory(
                id=1,
                guild_id="123456789",
                plan=SubscriptionPlan.PREMIUM,
                start_date=datetime.now() - timedelta(days=15),
                end_date=datetime.now() + timedelta(days=15),
                status="active",
                upgraded_by=owner_id,
                reason="Manual upgrade for testing"
            ),
            SubscriptionHistory(
                id=2,
                guild_id="987654321",
                plan=SubscriptionPlan.VIP,
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() + timedelta(days=25),
                status="active", 
                upgraded_by=owner_id,
                reason="VIP trial period"
            )
        ]
        
        revenue_summary = {
            "monthly_recurring": 129.97,
            "total_this_month": 259.94,
            "total_last_month": 189.96,
            "annual_projection": 1559.64
        }
        
        # Mock upcoming renewals and expired
        upcoming_renewals = []
        expired_subscriptions = []
        
        return SubscriptionManagement(
            active_subscriptions=active_subscriptions,
            revenue_summary=revenue_summary,
            upcoming_renewals=upcoming_renewals,
            expired_subscriptions=expired_subscriptions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading subscription management: {str(e)}")


@router.get("/health")
async def super_admin_health_check():
    """Health check para el módulo Super Admin"""
    
    try:
        db_path = get_db_path()
        
        # Test database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        
        return {
            "status": "healthy",
            "module": "super_admin",
            "database_connection": "ok",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "module": "super_admin", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }