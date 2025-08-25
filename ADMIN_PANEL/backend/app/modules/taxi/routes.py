from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import sqlite3
import math
import json
from .models import (
    TaxiConfig, TaxiConfigCreate, TaxiConfigUpdate,
    Vehicle, VehicleCreate, VehicleUpdate,
    Zone, ZoneCreate, ZoneUpdate,
    TaxiStop, TaxiStopCreate, TaxiStopUpdate,
    DriverLevel, DriverLevelCreate, DriverLevelUpdate,
    Pricing, PricingCreate, PricingUpdate,
    FareCalculationRequest, FareCalculationResponse
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

def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate distance between two points in kilometers"""
    # Simple Euclidean distance, converted to km (assuming SCUM coordinates)
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance / 1000.0  # Convert to km (adjust factor as needed)

# Taxi Configuration Endpoints
@router.get("/config", response_model=TaxiConfig)
async def get_taxi_config(guild_id: str = "123456789"):
    """Get taxi configuration for a guild"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, guild_id, taxi_channel_id, base_fare, per_km_rate,
                   commission_percent, max_distance_km, min_fare, waiting_time_rate,
                   night_multiplier, peak_hours_multiplier, peak_hours_start,
                   peak_hours_end, auto_accept_distance, driver_minimum_level,
                   is_active, created_at, updated_at, updated_by
            FROM admin_taxi_config 
            WHERE guild_id = ?
        """, (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Taxi configuration not found")
        
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching taxi config: {str(e)}")

@router.put("/config", response_model=TaxiConfig)
async def update_taxi_config(config: TaxiConfigUpdate, guild_id: str = "123456789"):
    """Update taxi configuration"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE admin_taxi_config SET
                taxi_channel_id = ?, base_fare = ?, per_km_rate = ?,
                commission_percent = ?, max_distance_km = ?, min_fare = ?,
                waiting_time_rate = ?, night_multiplier = ?, peak_hours_multiplier = ?,
                peak_hours_start = ?, peak_hours_end = ?, auto_accept_distance = ?,
                driver_minimum_level = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
        """, (
            config.taxi_channel_id, config.base_fare, config.per_km_rate,
            config.commission_percent, config.max_distance_km, config.min_fare,
            config.waiting_time_rate, config.night_multiplier, config.peak_hours_multiplier,
            config.peak_hours_start, config.peak_hours_end, config.auto_accept_distance,
            config.driver_minimum_level, config.is_active, guild_id
        ))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Taxi configuration not found")
        
        conn.commit()
        conn.close()
        
        return await get_taxi_config(guild_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating taxi config: {str(e)}")

# Vehicle Management Endpoints
@router.get("/vehicles", response_model=List[Vehicle])
async def get_vehicles(guild_id: str = "123456789"):
    """Get all vehicles for a guild"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, guild_id, vehicle_name, display_name, description,
                   base_multiplier, comfort_multiplier, speed_multiplier,
                   capacity_passengers, fuel_consumption, maintenance_cost,
                   unlock_level, purchase_cost, emoji, is_active, is_premium, created_at
            FROM admin_taxi_vehicles 
            WHERE guild_id = ? 
            ORDER BY unlock_level, vehicle_name
        """, (guild_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vehicles: {str(e)}")

@router.post("/vehicles", response_model=Vehicle)
async def create_vehicle(vehicle: VehicleCreate):
    """Create new vehicle type"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO admin_taxi_vehicles 
            (guild_id, vehicle_name, display_name, description, base_multiplier,
             comfort_multiplier, speed_multiplier, capacity_passengers,
             fuel_consumption, maintenance_cost, unlock_level, purchase_cost,
             emoji, is_active, is_premium)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vehicle.guild_id, vehicle.vehicle_name, vehicle.display_name,
            vehicle.description, vehicle.base_multiplier, vehicle.comfort_multiplier,
            vehicle.speed_multiplier, vehicle.capacity_passengers,
            vehicle.fuel_consumption, vehicle.maintenance_cost, vehicle.unlock_level,
            vehicle.purchase_cost, vehicle.emoji, vehicle.is_active, vehicle.is_premium
        ))
        
        vehicle_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return the created vehicle
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, guild_id, vehicle_name, display_name, description,
                   base_multiplier, comfort_multiplier, speed_multiplier,
                   capacity_passengers, fuel_consumption, maintenance_cost,
                   unlock_level, purchase_cost, emoji, is_active, is_premium, created_at
            FROM admin_taxi_vehicles 
            WHERE id = ?
        """, (vehicle_id,))
        
        result = cursor.fetchone()
        conn.close()
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating vehicle: {str(e)}")

@router.put("/vehicles/{vehicle_id}", response_model=Vehicle)
async def update_vehicle(vehicle_id: int, vehicle: VehicleUpdate, guild_id: str = "123456789"):
    """Update existing vehicle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE admin_taxi_vehicles SET
                vehicle_name = ?, display_name = ?, description = ?, base_multiplier = ?,
                comfort_multiplier = ?, speed_multiplier = ?, capacity_passengers = ?,
                fuel_consumption = ?, maintenance_cost = ?, unlock_level = ?,
                purchase_cost = ?, emoji = ?, is_active = ?, is_premium = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND guild_id = ?
        """, (
            vehicle.vehicle_name, vehicle.display_name, vehicle.description,
            vehicle.base_multiplier, vehicle.comfort_multiplier, vehicle.speed_multiplier,
            vehicle.capacity_passengers, vehicle.fuel_consumption, vehicle.maintenance_cost,
            vehicle.unlock_level, vehicle.purchase_cost, vehicle.emoji,
            vehicle.is_active, vehicle.is_premium, vehicle_id, guild_id
        ))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        conn.commit()
        conn.close()
        
        # Return updated vehicle
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, guild_id, vehicle_name, display_name, description,
                   base_multiplier, comfort_multiplier, speed_multiplier,
                   capacity_passengers, fuel_consumption, maintenance_cost,
                   unlock_level, purchase_cost, emoji, is_active, is_premium, created_at
            FROM admin_taxi_vehicles 
            WHERE id = ?
        """, (vehicle_id,))
        
        result = cursor.fetchone()
        conn.close()
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating vehicle: {str(e)}")

@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int, guild_id: str = "123456789"):
    """Delete vehicle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM admin_taxi_vehicles 
            WHERE id = ? AND guild_id = ?
        """, (vehicle_id, guild_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        conn.commit()
        conn.close()
        
        return {"message": "Vehicle deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting vehicle: {str(e)}")

# Zone Management Endpoints
@router.get("/zones", response_model=List[Zone])
async def get_zones(guild_id: str = "123456789"):
    """Get all zones for a guild"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, guild_id, zone_name, display_name, description, zone_type,
                   danger_multiplier, min_driver_level, allowed_vehicles,
                   restricted_hours, coordinate_bounds, warning_message,
                   requires_confirmation, is_active, created_at
            FROM admin_taxi_zones 
            WHERE guild_id = ? 
            ORDER BY zone_type, zone_name
        """, (guild_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching zones: {str(e)}")

@router.post("/zones", response_model=Zone)
async def create_zone(zone: ZoneCreate):
    """Create new zone"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO admin_taxi_zones 
            (guild_id, zone_name, display_name, description, zone_type,
             danger_multiplier, min_driver_level, allowed_vehicles,
             restricted_hours, coordinate_bounds, warning_message,
             requires_confirmation, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            zone.guild_id, zone.zone_name, zone.display_name, zone.description,
            zone.zone_type, zone.danger_multiplier, zone.min_driver_level,
            zone.allowed_vehicles, zone.restricted_hours, zone.coordinate_bounds,
            zone.warning_message, zone.requires_confirmation, zone.is_active
        ))
        
        zone_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return the created zone
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, guild_id, zone_name, display_name, description, zone_type,
                   danger_multiplier, min_driver_level, allowed_vehicles,
                   restricted_hours, coordinate_bounds, warning_message,
                   requires_confirmation, is_active, created_at
            FROM admin_taxi_zones 
            WHERE id = ?
        """, (zone_id,))
        
        result = cursor.fetchone()
        conn.close()
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating zone: {str(e)}")

@router.put("/zones/{zone_id}", response_model=Zone)
async def update_zone(zone_id: int, zone: ZoneUpdate, guild_id: str = "123456789"):
    """Update existing zone"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE admin_taxi_zones SET
                zone_name = ?, display_name = ?, description = ?, zone_type = ?,
                danger_multiplier = ?, min_driver_level = ?, allowed_vehicles = ?,
                restricted_hours = ?, coordinate_bounds = ?, warning_message = ?,
                requires_confirmation = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND guild_id = ?
        """, (
            zone.zone_name, zone.display_name, zone.description, zone.zone_type,
            zone.danger_multiplier, zone.min_driver_level, zone.allowed_vehicles,
            zone.restricted_hours, zone.coordinate_bounds, zone.warning_message,
            zone.requires_confirmation, zone.is_active, zone_id, guild_id
        ))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Zone not found")
        
        conn.commit()
        conn.close()
        
        # Return updated zone
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, guild_id, zone_name, display_name, description, zone_type,
                   danger_multiplier, min_driver_level, allowed_vehicles,
                   restricted_hours, coordinate_bounds, warning_message,
                   requires_confirmation, is_active, created_at
            FROM admin_taxi_zones 
            WHERE id = ?
        """, (zone_id,))
        
        result = cursor.fetchone()
        conn.close()
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating zone: {str(e)}")

@router.delete("/zones/{zone_id}")
async def delete_zone(zone_id: int, guild_id: str = "123456789"):
    """Delete zone"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM admin_taxi_zones 
            WHERE id = ? AND guild_id = ?
        """, (zone_id, guild_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Zone not found")
        
        conn.commit()
        conn.close()
        
        return {"message": "Zone deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting zone: {str(e)}")

# Taxi Stops Endpoints
@router.get("/stops", response_model=List[TaxiStop])
async def get_taxi_stops(guild_id: str = "123456789"):
    """Get all taxi stops for a guild"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, guild_id, stop_name, display_name, description,
                   coordinate_x, coordinate_y, coordinate_z, zone_id,
                   is_pickup_point, is_dropoff_point, popularity_bonus,
                   waiting_area_size, landmark_type, emoji, is_active, created_at
            FROM admin_taxi_stops 
            WHERE guild_id = ? 
            ORDER BY landmark_type, stop_name
        """, (guild_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching taxi stops: {str(e)}")

@router.post("/stops", response_model=TaxiStop)
async def create_taxi_stop(stop: TaxiStopCreate):
    """Create new taxi stop"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO admin_taxi_stops 
            (guild_id, stop_name, display_name, description, coordinate_x,
             coordinate_y, coordinate_z, zone_id, is_pickup_point,
             is_dropoff_point, popularity_bonus, waiting_area_size,
             landmark_type, emoji, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stop.guild_id, stop.stop_name, stop.display_name, stop.description,
            stop.coordinate_x, stop.coordinate_y, stop.coordinate_z, stop.zone_id,
            stop.is_pickup_point, stop.is_dropoff_point, stop.popularity_bonus,
            stop.waiting_area_size, stop.landmark_type, stop.emoji, stop.is_active
        ))
        
        stop_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return the created stop
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, guild_id, stop_name, display_name, description,
                   coordinate_x, coordinate_y, coordinate_z, zone_id,
                   is_pickup_point, is_dropoff_point, popularity_bonus,
                   waiting_area_size, landmark_type, emoji, is_active, created_at
            FROM admin_taxi_stops 
            WHERE id = ?
        """, (stop_id,))
        
        result = cursor.fetchone()
        conn.close()
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating taxi stop: {str(e)}")

@router.put("/stops/{stop_id}", response_model=TaxiStop)
async def update_taxi_stop(stop_id: int, stop: TaxiStopUpdate, guild_id: str = "123456789"):
    """Update existing taxi stop"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE admin_taxi_stops SET
                stop_name = ?, display_name = ?, description = ?, coordinate_x = ?,
                coordinate_y = ?, coordinate_z = ?, zone_id = ?, is_pickup_point = ?,
                is_dropoff_point = ?, popularity_bonus = ?, waiting_area_size = ?,
                landmark_type = ?, emoji = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND guild_id = ?
        """, (
            stop.stop_name, stop.display_name, stop.description, stop.coordinate_x,
            stop.coordinate_y, stop.coordinate_z, stop.zone_id, stop.is_pickup_point,
            stop.is_dropoff_point, stop.popularity_bonus, stop.waiting_area_size,
            stop.landmark_type, stop.emoji, stop.is_active, stop_id, guild_id
        ))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Taxi stop not found")
        
        conn.commit()
        conn.close()
        
        # Return updated stop
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, guild_id, stop_name, display_name, description,
                   coordinate_x, coordinate_y, coordinate_z, zone_id,
                   is_pickup_point, is_dropoff_point, popularity_bonus,
                   waiting_area_size, landmark_type, emoji, is_active, created_at
            FROM admin_taxi_stops 
            WHERE id = ?
        """, (stop_id,))
        
        result = cursor.fetchone()
        conn.close()
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating taxi stop: {str(e)}")

@router.delete("/stops/{stop_id}")
async def delete_taxi_stop(stop_id: int, guild_id: str = "123456789"):
    """Delete taxi stop"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM admin_taxi_stops 
            WHERE id = ? AND guild_id = ?
        """, (stop_id, guild_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Taxi stop not found")
        
        conn.commit()
        conn.close()
        
        return {"message": "Taxi stop deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting taxi stop: {str(e)}")

# Driver Levels Endpoints
@router.get("/driver-levels", response_model=List[DriverLevel])
async def get_driver_levels(guild_id: str = "123456789"):
    """Get all driver levels for a guild"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, guild_id, level, level_name, description, required_trips,
                   required_distance, earnings_multiplier, tip_multiplier,
                   unlock_vehicles, unlock_zones, special_perks, badge_emoji,
                   is_active, created_at
            FROM admin_taxi_driver_levels 
            WHERE guild_id = ? 
            ORDER BY level
        """, (guild_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching driver levels: {str(e)}")

# Pricing Rules Endpoints
@router.get("/pricing", response_model=List[Pricing])
async def get_pricing_rules(guild_id: str = "123456789"):
    """Get all pricing rules for a guild"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, guild_id, pricing_name, display_name, description,
                   pricing_type, multiplier_value, discount_amount, min_distance,
                   max_distance, applicable_zones, applicable_vehicles,
                   start_time, end_time, days_of_week, start_date, end_date,
                   priority, is_active, created_at
            FROM admin_taxi_pricing 
            WHERE guild_id = ? 
            ORDER BY priority DESC, pricing_name
        """, (guild_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pricing rules: {str(e)}")

# Fare Calculator Endpoint
@router.post("/calculate-fare", response_model=FareCalculationResponse)
async def calculate_fare(request: FareCalculationRequest, guild_id: str = "123456789"):
    """Calculate taxi fare based on parameters"""
    try:
        # Get taxi config
        config_data = await get_taxi_config(guild_id)
        
        # Get vehicle data
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT base_multiplier, comfort_multiplier 
            FROM admin_taxi_vehicles 
            WHERE guild_id = ? AND vehicle_name = ? AND is_active = TRUE
        """, (guild_id, request.vehicle_type))
        vehicle_data = cursor.fetchone()
        
        # Get zone data
        cursor.execute("""
            SELECT danger_multiplier 
            FROM admin_taxi_zones 
            WHERE guild_id = ? AND zone_type = ? AND is_active = TRUE
        """, (guild_id, request.zone_type))
        zone_data = cursor.fetchone()
        
        # Get driver level data
        cursor.execute("""
            SELECT earnings_multiplier 
            FROM admin_taxi_driver_levels 
            WHERE guild_id = ? AND level = ? AND is_active = TRUE
        """, (guild_id, request.driver_level))
        driver_data = cursor.fetchone()
        
        conn.close()
        
        # Calculate distance
        distance_km = calculate_distance(
            request.origin_x, request.origin_y,
            request.destination_x, request.destination_y
        )
        
        # Base calculations
        base_fare = config_data['base_fare']
        distance_fare = distance_km * config_data['per_km_rate']
        
        # Multipliers
        vehicle_multiplier = vehicle_data['base_multiplier'] if vehicle_data else 1.0
        zone_multiplier = zone_data['danger_multiplier'] if zone_data else 1.0
        driver_bonus = driver_data['earnings_multiplier'] if driver_data else 1.0
        
        # Time multipliers
        time_multiplier = 1.0
        if request.is_night_time:
            time_multiplier *= config_data['night_multiplier']
        if request.is_peak_hours:
            time_multiplier *= config_data['peak_hours_multiplier']
        
        # Calculate total before commission
        subtotal = (base_fare + distance_fare) * vehicle_multiplier * zone_multiplier * time_multiplier
        
        # Apply minimum fare
        subtotal = max(subtotal, config_data['min_fare'])
        
        # Calculate commission
        commission = subtotal * (config_data['commission_percent'] / 100)
        driver_earnings = (subtotal - commission) * driver_bonus
        
        breakdown = {
            "base_fare": base_fare,
            "distance_fare": distance_fare,
            "vehicle_bonus": (vehicle_multiplier - 1.0) * 100,
            "zone_bonus": (zone_multiplier - 1.0) * 100,
            "time_bonus": (time_multiplier - 1.0) * 100,
            "driver_bonus": (driver_bonus - 1.0) * 100,
            "commission_rate": config_data['commission_percent']
        }
        
        return FareCalculationResponse(
            base_fare=base_fare,
            distance_km=round(distance_km, 2),
            distance_fare=distance_fare,
            vehicle_multiplier=vehicle_multiplier,
            zone_multiplier=zone_multiplier,
            time_multiplier=time_multiplier,
            driver_bonus=driver_bonus,
            commission=round(commission, 2),
            total_fare=round(subtotal, 2),
            driver_earnings=round(driver_earnings, 2),
            breakdown=breakdown
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating fare: {str(e)}")