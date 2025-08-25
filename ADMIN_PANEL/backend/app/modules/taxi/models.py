from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

# Taxi Configuration Models
class TaxiConfigBase(BaseModel):
    taxi_channel_id: Optional[str] = None
    base_fare: float = Field(default=100.0, ge=0)
    per_km_rate: float = Field(default=25.0, ge=0)
    commission_percent: float = Field(default=10.0, ge=0, le=100)
    max_distance_km: float = Field(default=50.0, ge=0)
    min_fare: float = Field(default=50.0, ge=0)
    waiting_time_rate: float = Field(default=5.0, ge=0)
    night_multiplier: float = Field(default=1.2, ge=0)
    peak_hours_multiplier: float = Field(default=1.5, ge=0)
    peak_hours_start: str = Field(default="18:00")
    peak_hours_end: str = Field(default="22:00")
    auto_accept_distance: float = Field(default=5.0, ge=0)
    driver_minimum_level: int = Field(default=1, ge=1)
    is_active: bool = Field(default=True)

class TaxiConfigCreate(TaxiConfigBase):
    guild_id: str

class TaxiConfigUpdate(TaxiConfigBase):
    pass

class TaxiConfig(TaxiConfigBase):
    id: int
    guild_id: str
    created_at: datetime
    updated_at: datetime
    updated_by: int

    class Config:
        from_attributes = True

# Vehicle Models
class VehicleBase(BaseModel):
    vehicle_name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    base_multiplier: float = Field(default=1.0, ge=0)
    comfort_multiplier: float = Field(default=1.0, ge=0)
    speed_multiplier: float = Field(default=1.0, ge=0)
    capacity_passengers: int = Field(default=4, ge=1, le=20)
    fuel_consumption: float = Field(default=10.0, ge=0)
    maintenance_cost: float = Field(default=100.0, ge=0)
    unlock_level: int = Field(default=1, ge=1)
    purchase_cost: int = Field(default=5000, ge=0)
    emoji: str = Field(default="🚗")
    is_active: bool = Field(default=True)
    is_premium: bool = Field(default=False)

class VehicleCreate(VehicleBase):
    guild_id: str

class VehicleUpdate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    id: int
    guild_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Zone Models
class ZoneBase(BaseModel):
    zone_name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    zone_type: str = Field(default="safe")
    danger_multiplier: float = Field(default=1.0, ge=0)
    min_driver_level: int = Field(default=1, ge=1)
    allowed_vehicles: str = Field(default="all")
    restricted_hours: Optional[str] = None
    coordinate_bounds: Optional[str] = None
    warning_message: Optional[str] = None
    requires_confirmation: bool = Field(default=False)
    is_active: bool = Field(default=True)

class ZoneCreate(ZoneBase):
    guild_id: str

class ZoneUpdate(ZoneBase):
    pass

class Zone(ZoneBase):
    id: int
    guild_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Taxi Stop Models
class TaxiStopBase(BaseModel):
    stop_name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    coordinate_x: float = Field(...)
    coordinate_y: float = Field(...)
    coordinate_z: float = Field(default=0.0)
    zone_id: Optional[int] = None
    is_pickup_point: bool = Field(default=True)
    is_dropoff_point: bool = Field(default=True)
    popularity_bonus: float = Field(default=0.0)
    waiting_area_size: float = Field(default=50.0, ge=0)
    landmark_type: str = Field(default="general")
    emoji: str = Field(default="📍")
    is_active: bool = Field(default=True)

class TaxiStopCreate(TaxiStopBase):
    guild_id: str

class TaxiStopUpdate(TaxiStopBase):
    pass

class TaxiStop(TaxiStopBase):
    id: int
    guild_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Driver Level Models
class DriverLevelBase(BaseModel):
    level: int = Field(..., ge=1)
    level_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    required_trips: int = Field(default=0, ge=0)
    required_distance: float = Field(default=0.0, ge=0)
    earnings_multiplier: float = Field(default=1.0, ge=0)
    tip_multiplier: float = Field(default=1.0, ge=0)
    unlock_vehicles: str = Field(default="[]")
    unlock_zones: str = Field(default="[]")
    special_perks: str = Field(default="{}")
    badge_emoji: str = Field(default="🚗")
    is_active: bool = Field(default=True)

class DriverLevelCreate(DriverLevelBase):
    guild_id: str

class DriverLevelUpdate(DriverLevelBase):
    pass

class DriverLevel(DriverLevelBase):
    id: int
    guild_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Pricing Models
class PricingBase(BaseModel):
    pricing_name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    pricing_type: str = Field(default="multiplier")
    multiplier_value: float = Field(default=1.0, ge=0)
    discount_amount: float = Field(default=0.0, ge=0)
    min_distance: float = Field(default=0.0, ge=0)
    max_distance: float = Field(default=999999.0, ge=0)
    applicable_zones: str = Field(default="[]")
    applicable_vehicles: str = Field(default="[]")
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    days_of_week: str = Field(default="[]")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: int = Field(default=1, ge=1)
    is_active: bool = Field(default=True)

class PricingCreate(PricingBase):
    guild_id: str

class PricingUpdate(PricingBase):
    pass

class Pricing(PricingBase):
    id: int
    guild_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Fare Calculation Models
class FareCalculationRequest(BaseModel):
    origin_x: float
    origin_y: float
    destination_x: float
    destination_y: float
    vehicle_type: str
    zone_type: Optional[str] = "safe"
    driver_level: int = Field(default=1, ge=1)
    is_night_time: bool = Field(default=False)
    is_peak_hours: bool = Field(default=False)

class FareCalculationResponse(BaseModel):
    base_fare: float
    distance_km: float
    distance_fare: float
    vehicle_multiplier: float
    zone_multiplier: float
    time_multiplier: float
    driver_bonus: float
    commission: float
    total_fare: float
    driver_earnings: float
    breakdown: dict