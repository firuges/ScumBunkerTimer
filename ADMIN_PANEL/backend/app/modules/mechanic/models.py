"""
Modelos Pydantic para el Sistema Mecánico
Basado en las tablas existentes del bot Discord SCUM
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ================================
# CONFIGURACIÓN PRINCIPAL
# ================================

class MechanicConfig(BaseModel):
    id: int
    guild_id: str
    mechanic_channel_id: Optional[str] = None
    notification_channel_id: Optional[str] = None
    auto_assign_mechanics: bool = False
    require_payment_confirmation: bool = True
    max_pending_requests_per_user: int = 3
    service_timeout_hours: int = 24
    pvp_zone_surcharge_percent: int = 50
    default_vehicle_insurance_rate: float = 1000.0
    commission_percent: float = 10.0
    min_mechanic_level: int = 1
    max_concurrent_services: int = 10
    is_active: bool = True
    created_at: str
    updated_at: str
    updated_by: Optional[int] = None

class MechanicConfigUpdate(BaseModel):
    mechanic_channel_id: Optional[str] = None
    notification_channel_id: Optional[str] = None
    auto_assign_mechanics: bool = False
    require_payment_confirmation: bool = True
    max_pending_requests_per_user: int = Field(ge=1, le=10)
    service_timeout_hours: int = Field(ge=1, le=168)  # max 1 week
    pvp_zone_surcharge_percent: int = Field(ge=0, le=200)
    default_vehicle_insurance_rate: float = Field(ge=100.0, le=50000.0)
    commission_percent: float = Field(ge=0.0, le=50.0)
    min_mechanic_level: int = Field(ge=1, le=10)
    max_concurrent_services: int = Field(ge=1, le=50)
    is_active: bool = True

class MechanicConfigCreate(BaseModel):
    guild_id: str
    mechanic_channel_id: Optional[str] = None
    notification_channel_id: Optional[str] = None
    auto_assign_mechanics: bool = False
    require_payment_confirmation: bool = True
    max_pending_requests_per_user: int = 3
    service_timeout_hours: int = 24
    pvp_zone_surcharge_percent: int = 50
    default_vehicle_insurance_rate: float = 1000.0
    commission_percent: float = 10.0
    min_mechanic_level: int = 1
    max_concurrent_services: int = 10
    is_active: bool = True

# ================================
# MECÁNICOS REGISTRADOS
# ================================

class RegisteredMechanic(BaseModel):
    id: int
    discord_id: str
    discord_guild_id: str
    ingame_name: str
    registered_by: str
    registered_at: str
    status: str = "active"
    specialties: str = "insurance,repairs,maintenance"
    experience_level: str = "beginner"
    total_services: int = 0
    rating: float = 5.0

class MechanicCreate(BaseModel):
    discord_id: str
    discord_guild_id: str
    ingame_name: str
    registered_by: str
    status: str = "active"
    specialties: str = "insurance,repairs,maintenance"
    experience_level: str = "beginner"

class MechanicUpdate(BaseModel):
    ingame_name: Optional[str] = None
    status: Optional[str] = None
    specialties: Optional[str] = None
    experience_level: Optional[str] = None

# ================================
# SERVICIOS DE MECÁNICO
# ================================

class MechanicService(BaseModel):
    id: int
    service_id: str
    vehicle_insurance_id: Optional[str] = None
    service_type: str = "insurance"
    description: Optional[str] = None
    cost: int
    mechanic_discord_id: Optional[str] = None
    client_discord_id: str
    guild_id: str
    status: str = "pending"
    vehicle_id: str
    vehicle_type: str
    vehicle_location: str
    payment_method: str = "ingame"
    ingame_name: str
    client_display_name: Optional[str] = None
    created_at: str
    updated_at: str
    mechanic_assigned_at: Optional[str] = None
    completed_at: Optional[str] = None

class ServiceCreate(BaseModel):
    service_id: str
    vehicle_insurance_id: Optional[str] = None
    service_type: str = "insurance"
    description: Optional[str] = None
    cost: int
    client_discord_id: str
    guild_id: str
    vehicle_id: str
    vehicle_type: str
    vehicle_location: str
    payment_method: str = "ingame"
    ingame_name: str
    client_display_name: Optional[str] = None

class ServiceUpdate(BaseModel):
    status: Optional[str] = None
    mechanic_discord_id: Optional[str] = None
    description: Optional[str] = None
    cost: Optional[int] = None

# ================================
# PRECIOS DE VEHÍCULOS
# ================================

class VehiclePrice(BaseModel):
    id: int
    guild_id: str
    vehicle_type: str
    price: int
    updated_by: str
    updated_at: str
    is_active: bool = True
    price_multiplier: float = 1.0
    pvp_surcharge_percent: int = 50

class VehiclePriceUpdate(BaseModel):
    price: int = Field(ge=100, le=50000)
    price_multiplier: float = Field(ge=0.1, le=5.0)
    pvp_surcharge_percent: int = Field(ge=0, le=200)
    is_active: bool = True

class VehiclePriceCreate(BaseModel):
    guild_id: str
    vehicle_type: str
    price: int = Field(ge=100, le=50000)
    updated_by: str
    price_multiplier: float = Field(ge=0.1, le=5.0, default=1.0)
    pvp_surcharge_percent: int = Field(ge=0, le=200, default=50)
    is_active: bool = True

# ================================
# PREFERENCIAS DE MECÁNICO
# ================================

class MechanicPreferences(BaseModel):
    id: int
    discord_id: str
    discord_guild_id: str
    receive_notifications: bool = True
    notification_types: str = "all"
    work_schedule: str = "anytime"
    preferred_services: str = "insurance"
    max_concurrent_jobs: int = 5
    auto_accept_price_limit: int = 0
    updated_at: str

class PreferencesUpdate(BaseModel):
    receive_notifications: bool = True
    notification_types: str = "all"
    work_schedule: str = "anytime"
    preferred_services: str = "insurance"
    max_concurrent_jobs: int = Field(ge=1, le=20, default=5)
    auto_accept_price_limit: int = Field(ge=0, le=10000, default=0)

# ================================
# HISTORIAL DE SEGUROS
# ================================

class InsuranceHistory(BaseModel):
    id: int
    service_id: str
    client_discord_id: str
    mechanic_discord_id: Optional[str] = None
    guild_id: str
    vehicle_id: str
    vehicle_type: str
    cost: int
    payment_method: str
    status: str
    action: str
    action_by: str
    action_at: str
    notes: Optional[str] = None
    previous_status: Optional[str] = None

# ================================
# ESTADÍSTICAS Y REPORTES
# ================================

class MechanicStats(BaseModel):
    total_mechanics: int
    active_mechanics: int
    total_services: int
    pending_services: int
    completed_services: int
    total_revenue: float
    average_service_cost: float
    most_popular_vehicle_type: str
    busiest_mechanic: Optional[str] = None

class ServiceStats(BaseModel):
    service_id: str
    service_type: str
    cost: int
    status: str
    created_at: str
    completed_at: Optional[str] = None
    mechanic_name: Optional[str] = None
    client_name: str
    vehicle_type: str
    duration_hours: Optional[float] = None

# ================================
# REQUESTS COMPUESTOS
# ================================

class VehicleTypeStats(BaseModel):
    vehicle_type: str
    total_services: int
    total_revenue: float
    average_cost: float
    completion_rate: float

class MechanicPerformance(BaseModel):
    discord_id: str
    ingame_name: str
    total_services: int
    completed_services: int
    total_revenue: float
    average_rating: float
    completion_rate: float
    average_response_time_hours: float

# ================================
# BULK OPERATIONS
# ================================

class BulkPriceUpdate(BaseModel):
    vehicle_types: List[str]
    price_adjustment_percent: float = Field(ge=-50.0, le=200.0)
    updated_by: str

class BulkMechanicUpdate(BaseModel):
    mechanic_ids: List[str]
    status: Optional[str] = None
    experience_level: Optional[str] = None