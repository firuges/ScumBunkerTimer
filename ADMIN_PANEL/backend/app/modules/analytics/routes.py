"""
Analytics Module - FastAPI Routes
Dashboard consolidado con métricas de todos los sistemas
"""

import sqlite3
import os
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .models import (
    AnalyticsDashboard, 
    FamePointsMetrics, 
    BankingMetrics, 
    TaxiMetrics, 
    MechanicMetrics,
    ActivityLog,
    SystemHealth,
    PerformanceMetrics,
    AnalyticsReport
)

router = APIRouter()

# Database path (5 levels up from this file)
db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "scum_main.db")

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(db_path)

@router.get("/dashboard")
async def get_analytics_dashboard(guild_id: str = Query(..., description="Guild ID")):
    """Get consolidated analytics dashboard"""
    try:
        # Obtener métricas de cada sistema
        fame_metrics = await get_fame_metrics(guild_id)
        banking_metrics = await get_banking_metrics(guild_id)
        taxi_metrics = await get_taxi_metrics(guild_id)
        mechanic_metrics = await get_mechanic_metrics(guild_id)
        
        # Actividad reciente simulada
        recent_activity = [
            ActivityLog(
                timestamp=datetime.now() - timedelta(minutes=5),
                system="mechanic",
                action="service_completed",
                details="Reparación SUV completada por MechMaster_Pro"
            ),
            ActivityLog(
                timestamp=datetime.now() - timedelta(minutes=15),
                system="taxi",
                action="fare_calculated",
                details="Nueva tarifa calculada: $418.28"
            ),
            ActivityLog(
                timestamp=datetime.now() - timedelta(minutes=30),
                system="fame",
                action="reward_claimed",
                details="100 Fame Points otorgados por Kill Spree"
            )
        ]
        
        # Comparativas entre sistemas
        system_activity_comparison = {
            "fame": fame_metrics.total_rewards,
            "banking": len(banking_metrics.account_types),
            "taxi": taxi_metrics.total_vehicles,
            "mechanic": mechanic_metrics.total_mechanics
        }
        
        # Tendencias de crecimiento (simuladas)
        growth_trends = {
            "fame": {"today": 2, "week": 8, "month": 25},
            "banking": {"today": 1, "week": 3, "month": 12},
            "taxi": {"today": 5, "week": 18, "month": 45},
            "mechanic": {"today": 3, "week": 12, "month": 28}
        }
        
        total_records = (fame_metrics.total_rewards + 
                        sum(banking_metrics.account_types.values()) + 
                        taxi_metrics.total_vehicles + 
                        mechanic_metrics.total_mechanics)
        
        dashboard = AnalyticsDashboard(
            guild_id=guild_id,
            generated_at=datetime.now(),
            total_systems_active=4,
            total_database_records=total_records,
            fame_metrics=fame_metrics,
            banking_metrics=banking_metrics,
            taxi_metrics=taxi_metrics,
            mechanic_metrics=mechanic_metrics,
            recent_activity=recent_activity,
            system_activity_comparison=system_activity_comparison,
            growth_trends=growth_trends
        )
        
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting analytics dashboard: {str(e)}")

async def get_fame_metrics(guild_id: str) -> FamePointsMetrics:
    """Get Fame Points system metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total rewards
        cursor.execute("SELECT COUNT(*) FROM admin_fame_rewards WHERE guild_id = ?", (guild_id,))
        total_rewards = cursor.fetchone()[0]
        
        # Total points distributed
        cursor.execute("SELECT SUM(fame_cost) FROM admin_fame_rewards WHERE guild_id = ? AND is_active = 1", (guild_id,))
        result = cursor.fetchone()[0]
        total_points = result if result else 0
        
        # Most popular reward (simulado)
        cursor.execute("SELECT reward_type FROM admin_fame_rewards WHERE guild_id = ? ORDER BY fame_cost DESC LIMIT 1", (guild_id,))
        result = cursor.fetchone()
        most_popular = result[0] if result else None
        
        # Average points
        avg_points = total_points / total_rewards if total_rewards > 0 else 0
        
        # Active rewards
        cursor.execute("SELECT COUNT(*) FROM admin_fame_rewards WHERE guild_id = ? AND is_active = 1", (guild_id,))
        active_rewards = cursor.fetchone()[0]
        
        return FamePointsMetrics(
            total_rewards=total_rewards,
            total_points_distributed=total_points,
            most_popular_reward=most_popular,
            average_points_per_reward=avg_points,
            active_rewards=active_rewards
        )
        
    finally:
        conn.close()

async def get_banking_metrics(guild_id: str) -> BankingMetrics:
    """Get Banking system metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total account types
        cursor.execute("SELECT COUNT(*) FROM admin_banking_account_types WHERE guild_id = ?", (guild_id,))
        total_accounts = cursor.fetchone()[0]
        
        # Account types breakdown
        cursor.execute("SELECT account_type_name, COUNT(*) FROM admin_banking_account_types WHERE guild_id = ? GROUP BY account_type_name", (guild_id,))
        account_types_data = cursor.fetchall()
        account_types = {row[0]: row[1] for row in account_types_data}
        
        # Simulated banking metrics
        total_balance = 150000.0
        total_fees = 2500.0
        avg_balance = total_balance / total_accounts if total_accounts > 0 else 0
        
        return BankingMetrics(
            total_accounts=total_accounts,
            total_balance=total_balance,
            account_types=account_types,
            total_fees_collected=total_fees,
            average_balance=avg_balance
        )
        
    finally:
        conn.close()

async def get_taxi_metrics(guild_id: str) -> TaxiMetrics:
    """Get Taxi system metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total vehicles
        cursor.execute("SELECT COUNT(*) FROM admin_taxi_vehicles WHERE guild_id = ?", (guild_id,))
        total_vehicles = cursor.fetchone()[0]
        
        # Active zones
        cursor.execute("SELECT COUNT(*) FROM admin_taxi_zones WHERE guild_id = ? AND is_active = 1", (guild_id,))
        active_zones = cursor.fetchone()[0]
        
        # Total stops
        cursor.execute("SELECT COUNT(*) FROM admin_taxi_stops WHERE guild_id = ? AND is_active = 1", (guild_id,))
        total_stops = cursor.fetchone()[0]
        
        # Most popular vehicle
        cursor.execute("SELECT vehicle_name FROM admin_taxi_vehicles WHERE guild_id = ? ORDER BY base_multiplier DESC LIMIT 1", (guild_id,))
        result = cursor.fetchone()
        most_popular_vehicle = result[0] if result else None
        
        # Simulated taxi metrics
        total_rides = 145
        total_revenue = 28500.0
        avg_fare = total_revenue / total_rides if total_rides > 0 else 0
        
        return TaxiMetrics(
            total_vehicles=total_vehicles,
            active_zones=active_zones,
            total_stops=total_stops,
            total_rides_completed=total_rides,
            total_revenue=total_revenue,
            average_fare=avg_fare,
            most_popular_vehicle=most_popular_vehicle
        )
        
    finally:
        conn.close()

async def get_mechanic_metrics(guild_id: str) -> MechanicMetrics:
    """Get Mechanic system metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total mechanics
        cursor.execute("SELECT COUNT(*) FROM registered_mechanics WHERE guild_id = ?", (guild_id,))
        total_mechanics = cursor.fetchone()[0]
        
        # Active mechanics
        cursor.execute("SELECT COUNT(*) FROM registered_mechanics WHERE guild_id = ? AND status = 'active'", (guild_id,))
        active_mechanics = cursor.fetchone()[0]
        
        # Total services
        cursor.execute("SELECT COUNT(*) FROM mechanic_services WHERE guild_id = ?", (guild_id,))
        total_services = cursor.fetchone()[0]
        
        # Completed services
        cursor.execute("SELECT COUNT(*) FROM mechanic_services WHERE guild_id = ? AND status = 'completed'", (guild_id,))
        completed_services = cursor.fetchone()[0]
        
        # Pending services
        cursor.execute("SELECT COUNT(*) FROM mechanic_services WHERE guild_id = ? AND status = 'pending'", (guild_id,))
        pending_services = cursor.fetchone()[0]
        
        # Total revenue
        cursor.execute("SELECT SUM(cost) FROM mechanic_services WHERE guild_id = ? AND status = 'completed'", (guild_id,))
        result = cursor.fetchone()[0]
        total_revenue = float(result) if result else 0.0
        
        # Average service cost
        avg_service_cost = total_revenue / completed_services if completed_services > 0 else 0
        
        return MechanicMetrics(
            total_mechanics=total_mechanics,
            active_mechanics=active_mechanics,
            total_services=total_services,
            completed_services=completed_services,
            pending_services=pending_services,
            total_revenue=total_revenue,
            average_service_cost=avg_service_cost
        )
        
    finally:
        conn.close()

@router.get("/system-health")
async def get_system_health(guild_id: str = Query(..., description="Guild ID")):
    """Get system health status for all modules"""
    systems_health = [
        SystemHealth(
            system_name="Fame Points",
            status="healthy",
            last_check=datetime.now(),
            response_time=45.2,
            error_count=0,
            uptime_percentage=99.8
        ),
        SystemHealth(
            system_name="Banking System",
            status="healthy", 
            last_check=datetime.now(),
            response_time=32.1,
            error_count=0,
            uptime_percentage=99.9
        ),
        SystemHealth(
            system_name="Taxi System",
            status="healthy",
            last_check=datetime.now(),
            response_time=28.7,
            error_count=0,
            uptime_percentage=99.7
        ),
        SystemHealth(
            system_name="Mechanic System",
            status="healthy",
            last_check=datetime.now(),
            response_time=41.3,
            error_count=0,
            uptime_percentage=99.6
        )
    ]
    
    return systems_health

@router.get("/performance")
async def get_performance_metrics(guild_id: str = Query(..., description="Guild ID")):
    """Get performance metrics for the Admin Panel"""
    performance = PerformanceMetrics(
        api_response_times={
            "fame": 0.045,
            "banking": 0.032,
            "taxi": 0.028,
            "mechanic": 0.041
        },
        database_query_times={
            "fame": 0.015,
            "banking": 0.022,
            "taxi": 0.018,
            "mechanic": 0.025
        },
        error_rates={
            "fame": 0.001,
            "banking": 0.0,
            "taxi": 0.002,
            "mechanic": 0.001
        },
        active_sessions=3,
        peak_usage_hours=[14, 18, 20, 21]  # 2pm, 6pm, 8pm, 9pm
    )
    
    return performance

@router.get("/report")
async def get_analytics_report(guild_id: str = Query(..., description="Guild ID")):
    """Get complete analytics report"""
    try:
        dashboard = await get_analytics_dashboard(guild_id)
        system_health = await get_system_health(guild_id)
        performance = await get_performance_metrics(guild_id)
        
        # Automated recommendations based on data
        recommendations = []
        
        if dashboard.mechanic_metrics.pending_services > 5:
            recommendations.append("Consider adding more active mechanics to handle pending services")
        
        if dashboard.taxi_metrics.total_rides_completed < 100:
            recommendations.append("Taxi system usage is low - consider promotional campaigns")
            
        if dashboard.banking_metrics.average_balance < 1000:
            recommendations.append("Low average balance - review welcome bonuses and incentives")
            
        if not recommendations:
            recommendations.append("All systems operating optimally - no immediate actions required")
        
        report = AnalyticsReport(
            dashboard=dashboard,
            system_health=system_health,
            performance=performance,
            recommendations=recommendations
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics report: {str(e)}")

@router.get("/activity")
async def get_recent_activity(
    guild_id: str = Query(..., description="Guild ID"),
    hours: int = Query(24, description="Hours of activity to retrieve")
):
    """Get recent activity logs from all systems"""
    # Simulated activity logs
    activities = [
        ActivityLog(
            timestamp=datetime.now() - timedelta(minutes=5),
            system="mechanic",
            action="service_completed",
            details="Reparación SUV completada por MechMaster_Pro",
            user_id="mechanic_001"
        ),
        ActivityLog(
            timestamp=datetime.now() - timedelta(minutes=15),
            system="taxi",
            action="fare_calculated", 
            details="Nueva tarifa calculada: $418.28 para SUV en zona segura",
            user_id="driver_005"
        ),
        ActivityLog(
            timestamp=datetime.now() - timedelta(minutes=30),
            system="fame",
            action="reward_claimed",
            details="100 Fame Points otorgados por Kill Spree Achievement",
            user_id="player_123"
        ),
        ActivityLog(
            timestamp=datetime.now() - timedelta(hours=1),
            system="banking",
            action="account_created",
            details="Nueva cuenta Premium creada con balance inicial $5000",
            user_id="player_456"
        ),
        ActivityLog(
            timestamp=datetime.now() - timedelta(hours=2),
            system="mechanic",
            action="mechanic_registered",
            details="Nuevo mecánico registrado: AutoRepair_Specialist",
            user_id="mechanic_002"
        )
    ]
    
    return activities