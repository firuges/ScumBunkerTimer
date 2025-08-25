"""
Rutas API para el Sistema Mecánico
Integración con las tablas existentes del bot Discord SCUM
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import sqlite3
import os
from datetime import datetime, timedelta

from .models import (
    MechanicConfig, MechanicConfigCreate, MechanicConfigUpdate,
    RegisteredMechanic, MechanicCreate, MechanicUpdate,
    MechanicService, ServiceCreate, ServiceUpdate,
    VehiclePrice, VehiclePriceCreate, VehiclePriceUpdate,
    MechanicPreferences, PreferencesUpdate,
    InsuranceHistory, MechanicStats, ServiceStats,
    VehicleTypeStats, MechanicPerformance,
    BulkPriceUpdate
)

router = APIRouter()

def get_db_connection():
    """Get database connection to scum_main.db"""
    try:
        # Ruta relativa desde el backend hacia la raíz del proyecto
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "scum_main.db")
        db_path = os.path.abspath(db_path)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# ================================
# CONFIGURACIÓN PRINCIPAL
# ================================

@router.get("/config", response_model=MechanicConfig)
async def get_mechanic_config(guild_id: str = Query(default="123456789")):
    """Obtener configuración del sistema mecánico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM admin_mechanic_config 
            WHERE guild_id = ?
        """, (guild_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Mechanic configuration not found")
        
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching mechanic config: {str(e)}")

@router.put("/config", response_model=MechanicConfig)
async def update_mechanic_config(config: MechanicConfigUpdate, guild_id: str = Query(default="123456789")):
    """Actualizar configuración del sistema mecánico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE admin_mechanic_config SET
                mechanic_channel_id = ?, notification_channel_id = ?,
                auto_assign_mechanics = ?, require_payment_confirmation = ?,
                max_pending_requests_per_user = ?, service_timeout_hours = ?,
                pvp_zone_surcharge_percent = ?, default_vehicle_insurance_rate = ?,
                commission_percent = ?, min_mechanic_level = ?,
                max_concurrent_services = ?, is_active = ?,
                updated_at = datetime('now')
            WHERE guild_id = ?
        """, (
            config.mechanic_channel_id, config.notification_channel_id,
            config.auto_assign_mechanics, config.require_payment_confirmation,
            config.max_pending_requests_per_user, config.service_timeout_hours,
            config.pvp_zone_surcharge_percent, config.default_vehicle_insurance_rate,
            config.commission_percent, config.min_mechanic_level,
            config.max_concurrent_services, config.is_active,
            guild_id
        ))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Mechanic configuration not found")
        
        conn.commit()
        conn.close()
        
        return await get_mechanic_config(guild_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating mechanic config: {str(e)}")

@router.post("/config", response_model=MechanicConfig)
async def create_mechanic_config(config: MechanicConfigCreate):
    """Crear configuración del sistema mecánico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO admin_mechanic_config (
                guild_id, mechanic_channel_id, notification_channel_id,
                auto_assign_mechanics, require_payment_confirmation,
                max_pending_requests_per_user, service_timeout_hours,
                pvp_zone_surcharge_percent, default_vehicle_insurance_rate,
                commission_percent, min_mechanic_level, max_concurrent_services,
                is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config.guild_id, config.mechanic_channel_id, config.notification_channel_id,
            config.auto_assign_mechanics, config.require_payment_confirmation,
            config.max_pending_requests_per_user, config.service_timeout_hours,
            config.pvp_zone_surcharge_percent, config.default_vehicle_insurance_rate,
            config.commission_percent, config.min_mechanic_level, config.max_concurrent_services,
            config.is_active
        ))
        
        conn.commit()
        conn.close()
        
        return await get_mechanic_config(config.guild_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating mechanic config: {str(e)}")

# ================================
# MECÁNICOS REGISTRADOS
# ================================

@router.get("/mechanics", response_model=List[RegisteredMechanic])
async def get_mechanics(guild_id: str = Query(default="123456789"), status: Optional[str] = None):
    """Obtener lista de mecánicos registrados"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM registered_mechanics 
            WHERE discord_guild_id = ?
        """
        params = [guild_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY registered_at DESC"
        
        cursor.execute(query, params)
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching mechanics: {str(e)}")

@router.post("/mechanics", response_model=RegisteredMechanic)
async def create_mechanic(mechanic: MechanicCreate):
    """Registrar un nuevo mecánico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO registered_mechanics (
                discord_id, discord_guild_id, ingame_name, registered_by,
                status, specialties, experience_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            mechanic.discord_id, mechanic.discord_guild_id, mechanic.ingame_name,
            mechanic.registered_by, mechanic.status, mechanic.specialties,
            mechanic.experience_level
        ))
        
        mechanic_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Retornar el mecánico creado
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registered_mechanics WHERE id = ?", (mechanic_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating mechanic: {str(e)}")

@router.put("/mechanics/{mechanic_id}", response_model=RegisteredMechanic)
async def update_mechanic(mechanic_id: int, mechanic: MechanicUpdate):
    """Actualizar información de un mecánico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir query dinámicamente solo con campos proporcionados
        update_fields = []
        update_values = []
        
        if mechanic.ingame_name is not None:
            update_fields.append("ingame_name = ?")
            update_values.append(mechanic.ingame_name)
        
        if mechanic.status is not None:
            update_fields.append("status = ?")
            update_values.append(mechanic.status)
        
        if mechanic.specialties is not None:
            update_fields.append("specialties = ?")
            update_values.append(mechanic.specialties)
        
        if mechanic.experience_level is not None:
            update_fields.append("experience_level = ?")
            update_values.append(mechanic.experience_level)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_values.append(mechanic_id)
        
        cursor.execute(f"""
            UPDATE registered_mechanics 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """, update_values)
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Mechanic not found")
        
        conn.commit()
        conn.close()
        
        # Retornar mecánico actualizado
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registered_mechanics WHERE id = ?", (mechanic_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating mechanic: {str(e)}")

@router.delete("/mechanics/{mechanic_id}")
async def delete_mechanic(mechanic_id: int):
    """Eliminar un mecánico (cambiar status a inactive)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE registered_mechanics 
            SET status = 'inactive' 
            WHERE id = ?
        """, (mechanic_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Mechanic not found")
        
        conn.commit()
        conn.close()
        
        return {"message": "Mechanic deactivated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deactivating mechanic: {str(e)}")

# ================================
# SERVICIOS DE MECÁNICO
# ================================

@router.get("/services", response_model=List[MechanicService])
async def get_services(
    guild_id: str = Query(default="123456789"),
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """Obtener lista de servicios de mecánico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM mechanic_services 
            WHERE guild_id = ?
        """
        params = [guild_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching services: {str(e)}")

@router.get("/services/{service_id}", response_model=MechanicService)
async def get_service(service_id: str):
    """Obtener detalles de un servicio específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM mechanic_services WHERE service_id = ?", (service_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching service: {str(e)}")

@router.put("/services/{service_id}", response_model=MechanicService)
async def update_service(service_id: str, service: ServiceUpdate):
    """Actualizar estado de un servicio"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir query dinámicamente
        update_fields = []
        update_values = []
        
        if service.status is not None:
            update_fields.append("status = ?")
            update_values.append(service.status)
            
            # Si se cambia a completed, actualizar completed_at
            if service.status == "completed":
                update_fields.append("completed_at = datetime('now')")
        
        if service.mechanic_discord_id is not None:
            update_fields.append("mechanic_discord_id = ?")
            update_values.append(service.mechanic_discord_id)
            update_fields.append("mechanic_assigned_at = datetime('now')")
        
        if service.description is not None:
            update_fields.append("description = ?")
            update_values.append(service.description)
        
        if service.cost is not None:
            update_fields.append("cost = ?")
            update_values.append(service.cost)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = datetime('now')")
        update_values.append(service_id)
        
        cursor.execute(f"""
            UPDATE mechanic_services 
            SET {', '.join(update_fields)}
            WHERE service_id = ?
        """, update_values)
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Service not found")
        
        conn.commit()
        conn.close()
        
        return await get_service(service_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating service: {str(e)}")

# ================================
# PRECIOS DE VEHÍCULOS
# ================================

@router.get("/vehicle-prices", response_model=List[VehiclePrice])
async def get_vehicle_prices(guild_id: str = Query(default="123456789")):
    """Obtener precios de vehículos configurados"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM vehicle_prices 
            WHERE guild_id = ? AND is_active = 1
            ORDER BY vehicle_type
        """, (guild_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vehicle prices: {str(e)}")

@router.put("/vehicle-prices/{vehicle_type}", response_model=VehiclePrice)
async def update_vehicle_price(vehicle_type: str, price_update: VehiclePriceUpdate, guild_id: str = Query(default="123456789"), updated_by: str = Query(default="admin")):
    """Actualizar precio de un tipo de vehículo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE vehicle_prices SET
                price = ?, price_multiplier = ?, pvp_surcharge_percent = ?,
                is_active = ?, updated_by = ?, updated_at = datetime('now')
            WHERE guild_id = ? AND vehicle_type = ?
        """, (
            price_update.price, price_update.price_multiplier,
            price_update.pvp_surcharge_percent, price_update.is_active,
            updated_by, guild_id, vehicle_type
        ))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vehicle price not found")
        
        conn.commit()
        conn.close()
        
        # Retornar precio actualizado
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM vehicle_prices 
            WHERE guild_id = ? AND vehicle_type = ?
        """, (guild_id, vehicle_type))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating vehicle price: {str(e)}")

@router.post("/vehicle-prices", response_model=VehiclePrice)
async def create_vehicle_price(price_create: VehiclePriceCreate):
    """Crear precio para un nuevo tipo de vehículo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO vehicle_prices (
                guild_id, vehicle_type, price, updated_by,
                price_multiplier, pvp_surcharge_percent, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            price_create.guild_id, price_create.vehicle_type, price_create.price,
            price_create.updated_by, price_create.price_multiplier,
            price_create.pvp_surcharge_percent, price_create.is_active
        ))
        
        price_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Retornar precio creado
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicle_prices WHERE id = ?", (price_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating vehicle price: {str(e)}")

# ================================
# ESTADÍSTICAS
# ================================

@router.get("/stats", response_model=MechanicStats)
async def get_mechanic_stats(guild_id: str = Query(default="123456789")):
    """Obtener estadísticas del sistema mecánico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total y mecánicos activos
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   COUNT(CASE WHEN status = 'active' THEN 1 END) as active
            FROM registered_mechanics 
            WHERE discord_guild_id = ?
        """, (guild_id,))
        mechanics_stats = cursor.fetchone()
        
        # Servicios totales, pendientes y completados
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                   AVG(cost) as avg_cost,
                   SUM(CASE WHEN status = 'completed' THEN cost ELSE 0 END) as total_revenue
            FROM mechanic_services 
            WHERE guild_id = ?
        """, (guild_id,))
        services_stats = cursor.fetchone()
        
        # Tipo de vehículo más popular
        cursor.execute("""
            SELECT vehicle_type, COUNT(*) as count
            FROM mechanic_services 
            WHERE guild_id = ?
            GROUP BY vehicle_type
            ORDER BY count DESC
            LIMIT 1
        """, (guild_id,))
        popular_vehicle = cursor.fetchone()
        
        # Mecánico más activo
        cursor.execute("""
            SELECT rm.ingame_name, COUNT(ms.id) as services
            FROM registered_mechanics rm
            LEFT JOIN mechanic_services ms ON rm.discord_id = ms.mechanic_discord_id
            WHERE rm.discord_guild_id = ?
            GROUP BY rm.discord_id, rm.ingame_name
            ORDER BY services DESC
            LIMIT 1
        """, (guild_id,))
        busiest_mechanic = cursor.fetchone()
        
        conn.close()
        
        return MechanicStats(
            total_mechanics=mechanics_stats[0] or 0,
            active_mechanics=mechanics_stats[1] or 0,
            total_services=services_stats[0] or 0,
            pending_services=services_stats[1] or 0,
            completed_services=services_stats[2] or 0,
            average_service_cost=services_stats[3] or 0.0,
            total_revenue=services_stats[4] or 0.0,
            most_popular_vehicle_type=popular_vehicle[0] if popular_vehicle else "N/A",
            busiest_mechanic=busiest_mechanic[0] if busiest_mechanic else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching mechanic stats: {str(e)}")

@router.get("/stats/vehicles", response_model=List[VehicleTypeStats])
async def get_vehicle_type_stats(guild_id: str = Query(default="123456789")):
    """Obtener estadísticas por tipo de vehículo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                vehicle_type,
                COUNT(*) as total_services,
                SUM(CASE WHEN status = 'completed' THEN cost ELSE 0 END) as total_revenue,
                AVG(cost) as average_cost,
                CAST(COUNT(CASE WHEN status = 'completed' THEN 1 END) AS FLOAT) / COUNT(*) as completion_rate
            FROM mechanic_services 
            WHERE guild_id = ?
            GROUP BY vehicle_type
            ORDER BY total_services DESC
        """, (guild_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            VehicleTypeStats(
                vehicle_type=row[0],
                total_services=row[1],
                total_revenue=row[2] or 0.0,
                average_cost=row[3] or 0.0,
                completion_rate=row[4] or 0.0
            ) for row in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vehicle type stats: {str(e)}")

# ================================
# OPERACIONES MASIVAS
# ================================

@router.post("/bulk-price-update")
async def bulk_update_prices(bulk_update: BulkPriceUpdate, guild_id: str = Query(default="123456789")):
    """Actualizar precios de múltiples tipos de vehículos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updated_count = 0
        for vehicle_type in bulk_update.vehicle_types:
            cursor.execute("""
                UPDATE vehicle_prices 
                SET price = CAST(price * (1 + ? / 100.0) AS INTEGER),
                    updated_by = ?, updated_at = datetime('now')
                WHERE guild_id = ? AND vehicle_type = ?
            """, (
                bulk_update.price_adjustment_percent,
                bulk_update.updated_by,
                guild_id,
                vehicle_type
            ))
            updated_count += cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return {
            "message": f"Successfully updated prices for {updated_count} vehicle types",
            "adjustment_percent": bulk_update.price_adjustment_percent,
            "updated_types": bulk_update.vehicle_types
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bulk price update: {str(e)}")