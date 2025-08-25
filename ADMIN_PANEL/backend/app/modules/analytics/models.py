"""
Analytics Module - Pydantic Models
Dashboard consolidado con métricas de todos los sistemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class SystemMetrics(BaseModel):
    """Métricas generales de un sistema específico"""
    system_name: str
    total_records: int
    active_records: int
    created_today: int
    created_this_week: int
    created_this_month: int
    last_activity: Optional[datetime] = None

class FamePointsMetrics(BaseModel):
    """Métricas específicas del sistema Fame Points"""
    total_rewards: int
    total_points_distributed: int
    most_popular_reward: Optional[str] = None
    average_points_per_reward: float
    active_rewards: int

class BankingMetrics(BaseModel):
    """Métricas específicas del sistema Banking"""
    total_accounts: int
    total_balance: float
    account_types: Dict[str, int]  # {"Basic": 10, "Premium": 5, "VIP": 2}
    total_fees_collected: float
    average_balance: float

class TaxiMetrics(BaseModel):
    """Métricas específicas del sistema Taxi"""
    total_vehicles: int
    active_zones: int
    total_stops: int
    total_rides_completed: int
    total_revenue: float
    average_fare: float
    most_popular_vehicle: Optional[str] = None

class MechanicMetrics(BaseModel):
    """Métricas específicas del sistema Mechanic"""
    total_mechanics: int
    active_mechanics: int
    total_services: int
    completed_services: int
    pending_services: int
    total_revenue: float
    average_service_cost: float

class ActivityLog(BaseModel):
    """Log de actividad del sistema"""
    timestamp: datetime
    system: str
    action: str
    details: str
    user_id: Optional[str] = None

class AnalyticsDashboard(BaseModel):
    """Dashboard consolidado con todas las métricas"""
    guild_id: str
    generated_at: datetime
    
    # Métricas generales
    total_systems_active: int
    total_database_records: int
    
    # Métricas por sistema
    fame_metrics: FamePointsMetrics
    banking_metrics: BankingMetrics
    taxi_metrics: TaxiMetrics
    mechanic_metrics: MechanicMetrics
    
    # Actividad reciente
    recent_activity: List[ActivityLog]
    
    # Comparativas
    system_activity_comparison: Dict[str, int]
    growth_trends: Dict[str, Dict[str, int]]  # {"fame": {"today": 2, "week": 10}}

class SystemHealth(BaseModel):
    """Estado de salud de cada sistema"""
    system_name: str
    status: str  # "healthy", "warning", "error"
    last_check: datetime
    response_time: float  # en milisegundos
    error_count: int
    uptime_percentage: float

class PerformanceMetrics(BaseModel):
    """Métricas de rendimiento del Admin Panel"""
    api_response_times: Dict[str, float]  # {"fame": 0.05, "banking": 0.03}
    database_query_times: Dict[str, float]
    error_rates: Dict[str, float]
    active_sessions: int
    peak_usage_hours: List[int]

class AnalyticsReport(BaseModel):
    """Reporte completo de analytics"""
    dashboard: AnalyticsDashboard
    system_health: List[SystemHealth]
    performance: PerformanceMetrics
    recommendations: List[str]  # Recomendaciones automáticas