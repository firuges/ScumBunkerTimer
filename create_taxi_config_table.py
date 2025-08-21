#!/usr/bin/env python3
"""
Script para crear la tabla de configuración de taxi por servidor
"""

import aiosqlite
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def create_taxi_config_table():
    """Crear tabla de configuración de taxi por servidor"""
    
    print("CREANDO TABLA DE CONFIGURACION DE TAXI POR SERVIDOR")
    print("=" * 60)
    
    try:
        # Usar la base de datos del sistema de taxi
        db_path = "taxi_system.db"
        
        async with aiosqlite.connect(db_path) as db:
            # Crear tabla de configuración de taxi por servidor
            await db.execute("""
                CREATE TABLE IF NOT EXISTS taxi_server_config (
                    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL UNIQUE,
                    guild_name TEXT,
                    
                    -- Configuración general
                    feature_enabled BOOLEAN DEFAULT TRUE,
                    taxi_enabled BOOLEAN DEFAULT TRUE,
                    bank_enabled BOOLEAN DEFAULT TRUE,
                    welcome_pack_enabled BOOLEAN DEFAULT TRUE,
                    
                    -- Configuración económica
                    welcome_bonus REAL DEFAULT 7500.0,
                    taxi_base_rate REAL DEFAULT 500.0,
                    taxi_per_km_rate REAL DEFAULT 20.5,
                    taxi_wait_rate REAL DEFAULT 2.0,
                    driver_commission REAL DEFAULT 0.85,
                    platform_fee REAL DEFAULT 0.15,
                    
                    -- Tipos de vehículos (JSON)
                    vehicle_types TEXT DEFAULT NULL,
                    
                    -- Zonas del taxi (JSON)
                    taxi_stops TEXT DEFAULT NULL,
                    pvp_zones TEXT DEFAULT NULL,
                    
                    -- Configuración de niveles de conductor (JSON)
                    driver_levels TEXT DEFAULT NULL,
                    
                    -- Metadatos
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_modified_by TEXT DEFAULT NULL,
                    
                    -- Configuración adicional (JSON flexible)
                    additional_config TEXT DEFAULT NULL
                )
            """)
            
            print("OK - Tabla 'taxi_server_config' creada exitosamente")
            
            # Crear índices para optimización
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_taxi_config_guild_id 
                ON taxi_server_config(guild_id)
            """)
            
            print("OK - Indices creados")
            
            # Insertar configuración por defecto (template)
            default_vehicle_types = {
                "auto": {
                    "name": "Automóvil",
                    "emoji": "🚗",
                    "description": "Vehículo terrestre estándar",
                    "capacity": 4,
                    "speed_multiplier": 1.0,
                    "cost_multiplier": 1.0,
                    "access_types": ["land", "road"],
                    "restricted_zones": ["water", "air_only"]
                },
                "moto": {
                    "name": "Motocicleta", 
                    "emoji": "🏍️",
                    "description": "Vehículo rápido y ágil",
                    "capacity": 2,
                    "speed_multiplier": 1.3,
                    "cost_multiplier": 0.8,
                    "access_types": ["land", "road", "offroad"],
                    "restricted_zones": ["water", "air_only"]
                },
                "avion": {
                    "name": "Avión",
                    "emoji": "✈️", 
                    "description": "Transporte aéreo rápido",
                    "capacity": 2,
                    "speed_multiplier": 3.0,
                    "cost_multiplier": 3.5,
                    "access_types": ["air", "airstrip"],
                    "restricted_zones": ["water_only"],
                    "landing_zones": ["Z0-8", "A4-3", "B4-1", "A0-1"]
                },
                "hidroavion": {
                    "name": "Hidroavión",
                    "emoji": "🛩️",
                    "description": "Avión que aterriza en agua",
                    "capacity": 2,
                    "speed_multiplier": 2.5,
                    "cost_multiplier": 3.0,
                    "access_types": ["air", "water", "seaplane"],
                    "restricted_zones": [],
                    "landing_zones": ["water_zones"]
                },
                "barco": {
                    "name": "Barco",
                    "emoji": "🚢",
                    "description": "Transporte marítimo",
                    "capacity": 4,
                    "speed_multiplier": 0.8,
                    "cost_multiplier": 4.5,
                    "access_types": ["water", "port"],
                    "restricted_zones": ["land_only", "air_only"]
                }
            }
            
            default_driver_levels = {
                1: {"name": "Novato", "emoji": "🔰", "bonus": 0.0},
                5: {"name": "Experimentado", "emoji": "🟢", "bonus": 0.05},
                15: {"name": "Profesional", "emoji": "🔵", "bonus": 0.10},
                50: {"name": "Veterano", "emoji": "🟠", "bonus": 0.15},
                100: {"name": "Leyenda", "emoji": "🔴", "bonus": 0.25}
            }
            
            # Insertar configuración template (guild_id = 'default')
            await db.execute("""
                INSERT OR REPLACE INTO taxi_server_config 
                (guild_id, guild_name, vehicle_types, driver_levels, last_modified_by)
                VALUES (?, ?, ?, ?, ?)
            """, (
                'default',
                'Configuración por defecto',
                json.dumps(default_vehicle_types, ensure_ascii=False),
                json.dumps(default_driver_levels, ensure_ascii=False),
                'system'
            ))
            
            print("OK - Configuracion por defecto insertada")
            
            await db.commit()
            
            # Verificar la tabla
            cursor = await db.execute("SELECT COUNT(*) FROM taxi_server_config")
            count = await cursor.fetchone()
            print(f"OK - Tabla verificada: {count[0]} configuracion(es) en la base de datos")
            
            # Mostrar estructura de la tabla
            cursor = await db.execute("PRAGMA table_info(taxi_server_config)")
            columns = await cursor.fetchall()
            
            print(f"\nEstructura de la tabla 'taxi_server_config':")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                col_default = col[4] if col[4] else "NULL"
                print(f"   {col_name}: {col_type} (default: {col_default})")
        
        print(f"\nTABLA DE CONFIGURACION CREADA EXITOSAMENTE")
        print(f"Base de datos: {db_path}")
        print(f"Tabla: taxi_server_config")
        print(f"Configuración por defecto lista para usar")
        
        return True
        
    except Exception as e:
        print(f"\nERROR CREANDO TABLA: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal"""
    success = await create_taxi_config_table()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)