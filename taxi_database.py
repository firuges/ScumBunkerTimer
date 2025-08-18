#!/usr/bin/env python3
"""
Base de Datos del Sistema de Taxi Modular
Integrado con el sistema existente de SCUM Bot
"""

import aiosqlite
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import uuid

logger = logging.getLogger(__name__)

def detect_user_timezone(interaction=None) -> str:
    """
    Detectar el timezone del usuario basado en la información disponible.
    
    Para bot SCUM Uruguay, asumimos que la mayoría de usuarios están en Uruguay.
    En el futuro se puede expandir con detección más sofisticada.
    """
    try:
        # Para este bot específico de SCUM Uruguay, la mayoría de usuarios
        # probablemente están en Uruguay o zona horaria similar
        # Por simplicidad y exactitud, usamos America/Montevideo como default
        # ya que los servidores están configurados en este timezone
        
        import datetime
        
        # Detectar offset de timezone local del sistema
        local_time = datetime.datetime.now()
        utc_time = datetime.datetime.utcnow()
        offset_seconds = (local_time - utc_time).total_seconds()
        offset_hours = int(offset_seconds // 3600)
        
        logger.info(f"Sistema detectado con offset: {offset_hours}h")
        
        # Para usuarios de SCUM Uruguay, lo más probable es que estén en:
        # 1. Uruguay (America/Montevideo) - UTC-3
        # 2. Argentina (America/Argentina/Buenos_Aires) - UTC-3  
        # 3. Brasil (America/Sao_Paulo) - UTC-3
        
        # Mapeo mejorado con preferencia por zona Uruguay
        timezone_map = {
            -3: "America/Montevideo",  # Uruguay (principal)
            -5: "America/New_York",    # US Eastern
            -6: "America/Chicago",     # US Central  
            -8: "America/Los_Angeles", # US Pacific
            0: "UTC",                  # UTC
            1: "Europe/Madrid",        # España, Alemania
        }
        
        # Si encontramos un timezone conocido, usarlo
        if offset_hours in timezone_map:
            detected_tz = timezone_map[offset_hours]
            logger.info(f"Timezone detectado para usuario: {detected_tz} (offset: {offset_hours}h)")
            return detected_tz
        
        # Si no coincide con ningún offset conocido, pero estamos en bot Uruguay,
        # asumir que es Uruguay (la mayoría de usuarios)
        logger.info(f"Offset desconocido ({offset_hours}h), asumiendo Uruguay para bot SCUM")
        return "America/Montevideo"
        
    except Exception as e:
        logger.warning(f"Error detectando timezone: {e}, usando Uruguay por defecto")
        return "America/Montevideo"

def convert_time_to_user_timezone(time_str: str, from_timezone: str, to_timezone: str) -> str:
    """
    Convertir un tiempo de un timezone a otro timezone del usuario.
    
    Args:
        time_str: Tiempo en formato HH:MM
        from_timezone: Timezone origen (ej: "UTC", "America/Montevideo")
        to_timezone: Timezone destino del usuario
    
    Returns:
        Tiempo convertido en formato HH:MM con info del timezone
    """
    try:
        # Si ambos timezones son iguales, no hay necesidad de conversión
        if from_timezone == to_timezone:
            return time_str
        from zoneinfo import ZoneInfo
        from datetime import datetime, time
        
        # Parsear el tiempo
        hour, minute = map(int, time_str.split(':'))
        
        # Crear datetime de hoy con el tiempo especificado en el timezone origen
        today = datetime.now().date()
        dt_origin = datetime.combine(today, time(hour, minute))
        dt_origin = dt_origin.replace(tzinfo=ZoneInfo(from_timezone))
        
        # Convertir al timezone del usuario
        dt_user = dt_origin.astimezone(ZoneInfo(to_timezone))
        
        # Formatear resultado
        user_time = dt_user.strftime("%H:%M")
        
        # Agregar info adicional si es diferente día
        if dt_user.date() != dt_origin.date():
            if dt_user.date() > dt_origin.date():
                day_info = " (+1 día)"
            else:
                day_info = " (-1 día)"
            return f"{user_time}{day_info}"
        else:
            return user_time
            
    except ImportError:
        # Fallback si zoneinfo no está disponible (Python < 3.9)
        try:
            import pytz
            from datetime import datetime, time
            
            hour, minute = map(int, time_str.split(':'))
            today = datetime.now().date()
            
            # Crear datetime en timezone origen
            origin_tz = pytz.timezone(from_timezone)
            dt_origin = origin_tz.localize(datetime.combine(today, time(hour, minute)))
            
            # Convertir al timezone del usuario
            user_tz = pytz.timezone(to_timezone)
            dt_user = dt_origin.astimezone(user_tz)
            
            user_time = dt_user.strftime("%H:%M")
            
            if dt_user.date() != dt_origin.date():
                if dt_user.date() > dt_origin.date():
                    day_info = " (+1 día)"
                else:
                    day_info = " (-1 día)"
                return f"{user_time}{day_info}"
            else:
                return user_time
                
        except ImportError:
            # Si no hay pytz tampoco, retornar el tiempo original
            logger.warning("No se pudo convertir timezone: zoneinfo y pytz no disponibles")
            return f"{time_str} ({from_timezone})"
    except Exception as e:
        logger.error(f"Error convirtiendo timezone: {e}")
        return f"{time_str} ({from_timezone})"

class TaxiDatabase:
    def __init__(self, db_path: str = "taxi_system.db"):
        self.db_path = db_path

    async def initialize(self):
        """Inicializar todas las tablas del sistema"""
        async with aiosqlite.connect(self.db_path) as db:
            # === TABLA DE USUARIOS ===
            await db.execute("""
                CREATE TABLE IF NOT EXISTS taxi_users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id TEXT UNIQUE NOT NULL,
                    discord_guild_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    ingame_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    welcome_pack_claimed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # === SISTEMA BANCARIO ===
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    account_number TEXT UNIQUE NOT NULL,
                    account_type TEXT DEFAULT 'personal',
                    balance DECIMAL(15,2) DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_transaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES taxi_users(user_id) ON DELETE CASCADE
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bank_transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_uuid TEXT UNIQUE NOT NULL,
                    from_account TEXT,
                    to_account TEXT NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    transaction_type TEXT NOT NULL,
                    description TEXT,
                    reference_id TEXT,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_account) REFERENCES bank_accounts(account_number),
                    FOREIGN KEY (to_account) REFERENCES bank_accounts(account_number)
                )
            """)
            
            # === SISTEMA DE TAXI ===
            await db.execute("""
                CREATE TABLE IF NOT EXISTS taxi_drivers (
                    driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    license_number TEXT UNIQUE NOT NULL,
                    vehicle_type TEXT DEFAULT 'sedan',
                    vehicle_name TEXT,
                    status TEXT DEFAULT 'offline',
                    current_location_x DECIMAL(10,2),
                    current_location_y DECIMAL(10,2),
                    current_location_z DECIMAL(10,2),
                    rating DECIMAL(3,2) DEFAULT 5.00,
                    total_rides INTEGER DEFAULT 0,
                    total_earnings DECIMAL(15,2) DEFAULT 0.00,
                    earnings_today DECIMAL(10,2) DEFAULT 0.00,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES taxi_users(user_id) ON DELETE CASCADE
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS taxi_requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_uuid TEXT UNIQUE NOT NULL,
                    passenger_id INTEGER NOT NULL,
                    driver_id INTEGER,
                    pickup_x DECIMAL(10,2) NOT NULL,
                    pickup_y DECIMAL(10,2) NOT NULL,
                    pickup_z DECIMAL(10,2) NOT NULL,
                    pickup_zone TEXT,
                    destination_x DECIMAL(10,2),
                    destination_y DECIMAL(10,2),
                    destination_z DECIMAL(10,2),
                    destination_zone TEXT,
                    distance DECIMAL(10,2),
                    estimated_cost DECIMAL(10,2),
                    final_cost DECIMAL(10,2),
                    vehicle_type TEXT DEFAULT 'sedan',
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 0,
                    special_instructions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accepted_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    FOREIGN KEY (passenger_id) REFERENCES taxi_users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (driver_id) REFERENCES taxi_drivers(driver_id) ON DELETE SET NULL
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS taxi_ratings (
                    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL,
                    rater_id INTEGER NOT NULL,
                    rated_id INTEGER NOT NULL,
                    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                    comment TEXT,
                    rating_type TEXT NOT NULL, -- 'passenger_to_driver' or 'driver_to_passenger'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES taxi_requests(request_id) ON DELETE CASCADE,
                    FOREIGN KEY (rater_id) REFERENCES taxi_users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (rated_id) REFERENCES taxi_users(user_id) ON DELETE CASCADE
                )
            """)
            
            # === WELCOME PACKS ===
            await db.execute("""
                CREATE TABLE IF NOT EXISTS welcome_packs (
                    pack_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    pack_type TEXT DEFAULT 'standard',
                    cash_bonus DECIMAL(10,2) DEFAULT 5000.00,
                    items_given TEXT, -- JSON string
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES taxi_users(user_id) ON DELETE CASCADE
                )
            """)
            
            # === DAILY REWARDS ===
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_rewards (
                    reward_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount DECIMAL(10,2) DEFAULT 250.00,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES taxi_users(user_id) ON DELETE CASCADE
                )
            """)
            
            # === SHOP SYSTEM ===
            await db.execute("""
                CREATE TABLE IF NOT EXISTS shop_purchases (
                    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    pack_id TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    amount_paid DECIMAL(10,2),
                    payment_method TEXT DEFAULT 'money', -- 'money' or 'items'
                    payment_details TEXT, -- JSON string for alternative payments
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending', -- 'pending', 'delivered', 'cancelled'
                    delivered_at TIMESTAMP NULL,
                    delivered_by TEXT NULL, -- Discord ID del admin que entregó
                    guild_id TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES taxi_users(user_id) ON DELETE CASCADE
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS shop_stock (
                    stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pack_id TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    current_stock INTEGER DEFAULT 0,
                    max_stock INTEGER DEFAULT 5,
                    last_restock TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    next_restock TIMESTAMP,
                    UNIQUE(pack_id, tier)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS shop_cooldowns (
                    cooldown_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tier TEXT NOT NULL,
                    last_purchase TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    next_available TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES taxi_users(user_id) ON DELETE CASCADE,
                    UNIQUE(user_id, tier)
                )
            """)
            
            # === CONFIGURACIÓN ===
            await db.execute("""
                CREATE TABLE IF NOT EXISTS taxi_config (
                    config_key TEXT PRIMARY KEY,
                    config_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # === LOGS DEL SISTEMA ===
            await db.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_type TEXT NOT NULL,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    guild_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES taxi_users(user_id) ON DELETE SET NULL
                )
            """)
            
            # === CONFIGURACIÓN DE CANALES ===
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channel_config (
                    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    channel_type TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT,
                    UNIQUE(guild_id, channel_type)
                )
            """)
            
            # === CREAR ÍNDICES ===
            await db.execute("CREATE INDEX IF NOT EXISTS idx_taxi_users_discord_id ON taxi_users(discord_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_taxi_users_guild ON taxi_users(discord_guild_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_bank_accounts_user ON bank_accounts(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_bank_transactions_accounts ON bank_transactions(from_account, to_account)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_taxi_drivers_status ON taxi_drivers(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_taxi_requests_status ON taxi_requests(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_taxi_requests_passenger ON taxi_requests(passenger_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_taxi_requests_driver ON taxi_requests(driver_id)")
            
            # === MIGRACIONES DE ESQUEMA ===
            # Agregar updated_at a taxi_drivers si no existe
            try:
                cursor = await db.execute("PRAGMA table_info(taxi_drivers)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'updated_at' not in column_names:
                    # SQLite no permite CURRENT_TIMESTAMP en ALTER TABLE, usar datetime actual
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    await db.execute(f"ALTER TABLE taxi_drivers ADD COLUMN updated_at TIMESTAMP DEFAULT '{current_time}'")
                    logger.info("✅ Columna updated_at agregada a taxi_drivers")
            except Exception as e:
                logger.warning(f"No se pudo agregar columna updated_at: {e}")
            
            # Migración para shop_purchases - agregar columnas de entrega
            try:
                cursor = await db.execute("PRAGMA table_info(shop_purchases)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'delivered_at' not in column_names:
                    await db.execute("ALTER TABLE shop_purchases ADD COLUMN delivered_at TIMESTAMP NULL")
                    logger.info("✅ Columna delivered_at agregada a shop_purchases")
                
                if 'delivered_by' not in column_names:
                    await db.execute("ALTER TABLE shop_purchases ADD COLUMN delivered_by TEXT NULL")
                    logger.info("✅ Columna delivered_by agregada a shop_purchases")
                    
                if 'guild_id' not in column_names:
                    await db.execute("ALTER TABLE shop_purchases ADD COLUMN guild_id TEXT NOT NULL DEFAULT ''")
                    logger.info("✅ Columna guild_id agregada a shop_purchases")
                
                # Actualizar status por defecto para compras existentes
                await db.execute("UPDATE shop_purchases SET status = 'pending' WHERE status = 'completed'")
                logger.info("✅ Status de compras existentes actualizado a 'pending'")
                
            except Exception as e:
                logger.warning(f"Error en migración de shop_purchases: {e}")
            
            # Migración para taxi_users - agregar columna timezone
            try:
                cursor = await db.execute("PRAGMA table_info(taxi_users)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'timezone' not in column_names:
                    await db.execute("ALTER TABLE taxi_users ADD COLUMN timezone TEXT DEFAULT 'UTC'")
                    logger.info("✅ Columna timezone agregada a taxi_users")
                
            except Exception as e:
                logger.warning(f"Error en migración de timezone en taxi_users: {e}")
            
            # === TABLAS DEL SISTEMA DE ALERTAS DE REINICIO ===
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reset_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_name TEXT NOT NULL,
                    reset_time TEXT NOT NULL,  -- Formato HH:MM
                    timezone TEXT DEFAULT 'UTC',
                    days_of_week TEXT DEFAULT '1,2,3,4,5,6,7',  -- 1=Lunes, 7=Domingo
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (server_name) REFERENCES servers(server_name)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_reset_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    server_name TEXT NOT NULL,
                    alert_enabled BOOLEAN DEFAULT 1,
                    minutes_before INTEGER DEFAULT 15,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, guild_id, server_name),
                    FOREIGN KEY (server_name) REFERENCES servers(server_name)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reset_alert_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    server_name TEXT NOT NULL,
                    schedule_id INTEGER NOT NULL,
                    alert_date TEXT NOT NULL,  -- Format YYYY-MM-DD
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, guild_id, server_name, schedule_id, alert_date)
                )
            """)
            
            logger.info("✅ Tablas del sistema de alertas de reinicio creadas")
            
            # === MIGRACIONES ===
            # Agregar columna ingame_name si no existe
            try:
                cursor = await db.execute("PRAGMA table_info(taxi_users)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'ingame_name' not in column_names:
                    await db.execute("ALTER TABLE taxi_users ADD COLUMN ingame_name TEXT")
                    logger.info("✅ Migración: Columna ingame_name agregada a taxi_users")
            except Exception as e:
                logger.error(f"Error en migración ingame_name: {e}")
            
            await db.commit()
            logger.info("✅ Base de datos del sistema de taxi inicializada")

    # === GESTIÓN DE USUARIOS ===
    
    async def register_user(self, discord_id: str, guild_id: str, username: str, display_name: str = None, timezone: str = None, ingame_name: str = None) -> Tuple[bool, Dict]:
        """Registrar nuevo usuario con welcome pack"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Verificar si ya existe
                cursor = await db.execute(
                    "SELECT user_id FROM taxi_users WHERE discord_id = ? AND discord_guild_id = ?",
                    (discord_id, guild_id)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    return False, {"error": "Usuario ya registrado"}
                
                # Detectar timezone si no se proporciona
                if timezone is None:
                    timezone = detect_user_timezone()
                
                # Registrar usuario
                cursor = await db.execute("""
                    INSERT INTO taxi_users (discord_id, discord_guild_id, username, display_name, welcome_pack_claimed, timezone, ingame_name)
                    VALUES (?, ?, ?, ?, TRUE, ?, ?)
                """, (discord_id, guild_id, username, display_name, timezone, ingame_name))
                
                user_id = cursor.lastrowid
                
                # Generar número de cuenta
                account_number = f"TAX{user_id:06d}"
                
                # Crear cuenta bancaria con welcome bonus
                from taxi_config import taxi_config
                welcome_bonus = taxi_config.WELCOME_BONUS if taxi_config.WELCOME_PACK_ENABLED else 0
                
                await db.execute("""
                    INSERT INTO bank_accounts (user_id, account_number, balance)
                    VALUES (?, ?, ?)
                """, (user_id, account_number, welcome_bonus))
                
                # Registrar welcome pack
                welcome_items = {
                    "cash": welcome_bonus,
                    "taxi_vouchers": 3,
                    "premium_trial": 7
                }
                
                await db.execute("""
                    INSERT INTO welcome_packs (user_id, cash_bonus, items_given)
                    VALUES (?, ?, ?)
                """, (user_id, welcome_bonus, json.dumps(welcome_items)))
                
                # Transacción del welcome bonus
                if welcome_bonus > 0:
                    transaction_uuid = str(uuid.uuid4())
                    await db.execute("""
                        INSERT INTO bank_transactions 
                        (transaction_uuid, to_account, amount, transaction_type, description)
                        VALUES (?, ?, ?, 'welcome_bonus', 'Bono de bienvenida - Nuevo usuario')
                    """, (transaction_uuid, account_number, welcome_bonus))
                
                # Log del registro
                await db.execute("""
                    INSERT INTO system_logs (log_type, user_id, action, details, guild_id)
                    VALUES ('registration', ?, 'user_registered', ?, ?)
                """, (user_id, f"Usuario {username} registrado con bono de ${welcome_bonus}", guild_id))
                
                await db.commit()
                
                return True, {
                    "user_id": user_id,
                    "account_number": account_number,
                    "welcome_bonus": welcome_bonus,
                    "items": welcome_items
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error registrando usuario: {e}")
                return False, {"error": str(e)}

    async def get_user_by_discord_id(self, discord_id: str, guild_id: str) -> Optional[Dict]:
        """Obtener usuario por Discord ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT tu.user_id, tu.discord_id, tu.discord_guild_id, tu.username, tu.display_name, 
                       tu.joined_at, tu.last_active, tu.status, tu.welcome_pack_claimed, tu.created_at, 
                       tu.timezone, tu.ingame_name, ba.account_number, ba.balance
                FROM taxi_users tu
                LEFT JOIN bank_accounts ba ON tu.user_id = ba.user_id
                WHERE tu.discord_id = ? AND tu.discord_guild_id = ?
            """, (discord_id, guild_id))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            return {
                "user_id": row[0],
                "discord_id": row[1],
                "discord_guild_id": row[2],
                "username": row[3],
                "display_name": row[4],
                "joined_at": row[5],
                "last_active": row[6],
                "status": row[7],
                "welcome_pack_claimed": bool(row[8]),
                "created_at": row[9],
                "timezone": row[10] if len(row) > 10 and row[10] else "UTC",
                "ingame_name": row[11] if len(row) > 11 and row[11] else None,
                "account_number": row[12] if len(row) > 12 else None,
                "balance": float(row[13]) if len(row) > 13 and row[13] else 0.0
            }

    async def update_user_timezone(self, discord_id: str, guild_id: str, timezone: str) -> bool:
        """Actualizar el timezone de un usuario"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute("""
                    UPDATE taxi_users 
                    SET timezone = ? 
                    WHERE discord_id = ? AND discord_guild_id = ?
                """, (timezone, discord_id, guild_id))
                
                await db.commit()
                return cursor.rowcount > 0
                
            except Exception as e:
                logger.error(f"Error actualizando timezone de usuario: {e}")
                return False

    async def save_channel_config(self, guild_id: str, channel_type: str, channel_id: str, updated_by: str = None) -> bool:
        """Guardar configuración de canal en base de datos"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute("""
                    INSERT OR REPLACE INTO channel_config (guild_id, channel_type, channel_id, updated_by)
                    VALUES (?, ?, ?, ?)
                """, (guild_id, channel_type, channel_id, updated_by))
                
                await db.commit()
                logger.info(f"Configuración de canal guardada: {channel_type} en guild {guild_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error guardando configuración de canal: {e}")
                return False

    async def get_channel_config(self, guild_id: str, channel_type: str = None) -> dict:
        """Obtener configuración de canales de la base de datos"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                if channel_type:
                    # Obtener configuración específica
                    cursor = await db.execute("""
                        SELECT channel_type, channel_id, updated_at, updated_by 
                        FROM channel_config 
                        WHERE guild_id = ? AND channel_type = ?
                    """, (guild_id, channel_type))
                    row = await cursor.fetchone()
                    
                    if row:
                        return {
                            "channel_type": row[0],
                            "channel_id": row[1],
                            "updated_at": row[2],
                            "updated_by": row[3]
                        }
                    return {}
                else:
                    # Obtener todas las configuraciones del guild
                    cursor = await db.execute("""
                        SELECT channel_type, channel_id, updated_at, updated_by 
                        FROM channel_config 
                        WHERE guild_id = ?
                    """, (guild_id,))
                    rows = await cursor.fetchall()
                    
                    configs = {}
                    for row in rows:
                        configs[row[0]] = {
                            "channel_id": row[1],
                            "updated_at": row[2],
                            "updated_by": row[3]
                        }
                    return configs
                
            except Exception as e:
                logger.error(f"Error obteniendo configuración de canales: {e}")
                return {}

    async def load_all_channel_configs(self) -> dict:
        """Cargar todas las configuraciones de canales al iniciar el bot"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute("""
                    SELECT guild_id, channel_type, channel_id 
                    FROM channel_config
                """)
                rows = await cursor.fetchall()
                
                configs = {}
                for row in rows:
                    guild_id = row[0]
                    channel_type = row[1]
                    channel_id = int(row[2])
                    
                    if guild_id not in configs:
                        configs[guild_id] = {}
                    configs[guild_id][channel_type] = channel_id
                
                logger.info(f"Cargadas configuraciones de canales para {len(configs)} guilds")
                return configs
                
            except Exception as e:
                logger.error(f"Error cargando configuraciones de canales: {e}")
                return {}

    # === SISTEMA BANCARIO ===
    
    async def transfer_money(self, from_account: str, to_account: str, amount: float, 
                           description: str = "", reference_id: str = None) -> Tuple[bool, str]:
        """Transferir dinero entre cuentas"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Verificar saldo suficiente
                cursor = await db.execute(
                    "SELECT balance FROM bank_accounts WHERE account_number = ? AND status = 'active'",
                    (from_account,)
                )
                from_balance = await cursor.fetchone()
                
                if not from_balance or from_balance[0] < amount:
                    return False, "Saldo insuficiente"
                
                # Verificar cuenta destino
                cursor = await db.execute(
                    "SELECT account_number FROM bank_accounts WHERE account_number = ? AND status = 'active'",
                    (to_account,)
                )
                if not await cursor.fetchone():
                    return False, "Cuenta destino no encontrada"
                
                # Realizar transferencia
                await db.execute("""
                    UPDATE bank_accounts 
                    SET balance = balance - ?, last_transaction = CURRENT_TIMESTAMP
                    WHERE account_number = ?
                """, (amount, from_account))
                
                await db.execute("""
                    UPDATE bank_accounts 
                    SET balance = balance + ?, last_transaction = CURRENT_TIMESTAMP
                    WHERE account_number = ?
                """, (amount, to_account))
                
                # Registrar transacción
                transaction_uuid = str(uuid.uuid4())
                await db.execute("""
                    INSERT INTO bank_transactions 
                    (transaction_uuid, from_account, to_account, amount, transaction_type, description, reference_id)
                    VALUES (?, ?, ?, ?, 'transfer', ?, ?)
                """, (transaction_uuid, from_account, to_account, amount, description, reference_id))
                
                await db.commit()
                return True, "Transferencia exitosa"
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error en transferencia: {e}")
                return False, str(e)

    # === SISTEMA DE TAXI ===
    
    async def register_driver(self, user_id: int, vehicle_type: str = "sedan", vehicle_name: str = None) -> Tuple[bool, str]:
        """Registrar conductor de taxi"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Verificar si ya es conductor
                cursor = await db.execute(
                    "SELECT driver_id FROM taxi_drivers WHERE user_id = ?",
                    (user_id,)
                )
                if await cursor.fetchone():
                    return False, "Ya estás registrado como conductor"
                
                # Generar licencia
                license_number = f"DRV{user_id:06d}"
                
                # Registrar conductor
                await db.execute("""
                    INSERT INTO taxi_drivers (user_id, license_number, vehicle_type, vehicle_name)
                    VALUES (?, ?, ?, ?)
                """, (user_id, license_number, vehicle_type, vehicle_name))
                
                await db.commit()
                return True, license_number
                
            except Exception as e:
                await db.rollback()
                return False, str(e)

    async def get_driver_info(self, user_id: int) -> dict:
        """Obtener información del conductor"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute("""
                    SELECT driver_id, user_id, license_number, vehicle_type, vehicle_name, 
                           status, rating, total_rides, total_earnings, created_at
                    FROM taxi_drivers 
                    WHERE user_id = ?
                """, (user_id,))
                
                row = await cursor.fetchone()
                if row:
                    # Manejar vehículos múltiples
                    vehicle_data = row[3]  # vehicle_type field
                    vehicles = []
                    
                    if vehicle_data:
                        try:
                            import json
                            # Intentar parsear como JSON (nuevo formato)
                            vehicles = json.loads(vehicle_data)
                        except:
                            # Si falla, es formato antiguo (un solo vehículo)
                            vehicles = [vehicle_data]
                    
                    return {
                        'driver_id': row[0],
                        'user_id': row[1],
                        'license_number': row[2],
                        'vehicle_type': row[3],  # Campo raw para compatibilidad
                        'vehicle_name': row[4],
                        'status': row[5],
                        'rating': row[6],
                        'total_rides': row[7],
                        'total_earnings': row[8],
                        'created_at': row[9],
                        'vehicles': vehicles  # Lista de vehículos
                    }
                return None
                
            except Exception as e:
                logger.error(f"Error obteniendo info del conductor: {e}")
                return None

    async def create_taxi_request(self, passenger_id: int, pickup_x: float, pickup_y: float, pickup_z: float,
                                destination_x: float = None, destination_y: float = None, destination_z: float = None,
                                vehicle_type: str = "sedan", special_instructions: str = None) -> Tuple[bool, Dict]:
        """Crear solicitud de taxi"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Verificar que no tenga viaje activo
                cursor = await db.execute("""
                    SELECT request_id FROM taxi_requests 
                    WHERE passenger_id = ? AND status IN ('pending', 'accepted', 'in_progress')
                """, (passenger_id,))
                
                if await cursor.fetchone():
                    return False, {"error": "Ya tienes un viaje activo"}
                
                # Calcular datos del viaje
                from taxi_config import taxi_config
                
                # Verificar zonas
                pickup_zone = taxi_config.get_zone_at_location(pickup_x, pickup_y)
                can_pickup, pickup_message = taxi_config.can_pickup_at(pickup_x, pickup_y)
                
                if not can_pickup:
                    return False, {"error": pickup_message}
                
                distance = None
                estimated_cost = None
                destination_zone = None
                
                if all([destination_x, destination_y, destination_z]):
                    destination_zone = taxi_config.get_zone_at_location(destination_x, destination_y)
                    can_dropoff, dropoff_message = taxi_config.can_dropoff_at(destination_x, destination_y)
                    
                    if not can_dropoff:
                        return False, {"error": dropoff_message}
                    
                    # Validar la ruta según el tipo de vehículo
                    route_valid, route_message = await self.validate_route(pickup_zone, destination_zone, vehicle_type)
                    if not route_valid:
                        return False, {"error": route_message}
                    
                    distance = taxi_config.calculate_distance(pickup_x, pickup_y, destination_x, destination_y)
                    estimated_cost = taxi_config.calculate_fare(distance, vehicle_type)
                
                # Crear solicitud
                request_uuid = str(uuid.uuid4())
                cursor = await db.execute("""
                    INSERT INTO taxi_requests 
                    (request_uuid, passenger_id, pickup_x, pickup_y, pickup_z, pickup_zone,
                     destination_x, destination_y, destination_z, destination_zone,
                     distance, estimated_cost, vehicle_type, special_instructions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (request_uuid, passenger_id, pickup_x, pickup_y, pickup_z, pickup_zone["zone_name"],
                      destination_x, destination_y, destination_z, 
                      destination_zone["zone_name"] if destination_zone else None,
                      distance, estimated_cost, vehicle_type, special_instructions))
                
                request_id = cursor.lastrowid
                await db.commit()
                
                return True, {
                    "request_id": request_id,
                    "request_uuid": request_uuid,
                    "pickup_zone": pickup_zone,
                    "destination_zone": destination_zone,
                    "distance": distance,
                    "estimated_cost": estimated_cost
                }
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error creando solicitud de taxi: {e}")
                return False, {"error": str(e)}

    # === ESTADÍSTICAS ===
    
    async def get_system_stats(self, guild_id: str = None) -> Dict:
        """Obtener estadísticas del sistema"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Filtro por guild si se especifica
            guild_filter = "WHERE discord_guild_id = ?" if guild_id else ""
            guild_params = (guild_id,) if guild_id else ()
            
            # Usuarios registrados
            cursor = await db.execute(f"SELECT COUNT(*) FROM taxi_users {guild_filter}", guild_params)
            stats['total_users'] = (await cursor.fetchone())[0]
            
            # Conductores registrados
            if guild_id:
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM taxi_drivers td
                    JOIN taxi_users tu ON td.user_id = tu.user_id
                    WHERE tu.discord_guild_id = ?
                """, (guild_id,))
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM taxi_drivers")
            stats['total_drivers'] = (await cursor.fetchone())[0]
            
            # Viajes completados
            if guild_id:
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM taxi_requests tr
                    JOIN taxi_users tu ON tr.passenger_id = tu.user_id
                    WHERE tu.discord_guild_id = ? AND tr.status = 'completed'
                """, (guild_id,))
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM taxi_requests WHERE status = 'completed'")
            stats['completed_rides'] = (await cursor.fetchone())[0]
            
            # Dinero en circulación
            if guild_id:
                cursor = await db.execute("""
                    SELECT COALESCE(SUM(ba.balance), 0) FROM bank_accounts ba
                    JOIN taxi_users tu ON ba.user_id = tu.user_id
                    WHERE tu.discord_guild_id = ? AND ba.status = 'active'
                """, (guild_id,))
            else:
                cursor = await db.execute("SELECT COALESCE(SUM(balance), 0) FROM bank_accounts WHERE status = 'active'")
            stats['total_money'] = float((await cursor.fetchone())[0])
            
            # Conductores activos
            if guild_id:
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM taxi_drivers td
                    JOIN taxi_users tu ON td.user_id = tu.user_id
                    WHERE tu.discord_guild_id = ? AND td.status = 'online'
                """, (guild_id,))
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM taxi_drivers WHERE status = 'online'")
            stats['active_drivers'] = (await cursor.fetchone())[0]
            
            return stats

    async def get_pending_requests(self, exclude_user_id: int = None) -> List[dict]:
        """Obtener solicitudes pendientes (excluyendo las del usuario especificado)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                if exclude_user_id:
                    cursor = await db.execute("""
                        SELECT request_id, passenger_id, pickup_zone, destination_zone, 
                               estimated_cost, vehicle_type, created_at, special_instructions
                        FROM taxi_requests 
                        WHERE status = 'pending' AND passenger_id != ?
                        ORDER BY created_at ASC
                    """, (exclude_user_id,))
                else:
                    cursor = await db.execute("""
                        SELECT request_id, passenger_id, pickup_zone, destination_zone, 
                               estimated_cost, vehicle_type, created_at, special_instructions
                        FROM taxi_requests 
                        WHERE status = 'pending'
                        ORDER BY created_at ASC
                    """)
                
                requests = []
                async for row in cursor:
                    requests.append({
                        'request_id': row[0],
                        'passenger_id': row[1],
                        'pickup_zone': row[2],
                        'destination_zone': row[3],
                        'estimated_cost': row[4],
                        'vehicle_type': row[5],
                        'created_at': row[6],
                        'special_instructions': row[7]
                    })
                
                logger.debug(f"📋 Encontradas {len(requests)} solicitudes pendientes")
                return requests
                
            except Exception as e:
                logger.error(f"Error obteniendo solicitudes pendientes: {e}")
                return []
                
                return requests
                
            except Exception as e:
                logger.error(f"Error obteniendo solicitudes pendientes: {e}")
                return []

    async def get_active_request_for_user(self, user_id: int) -> dict:
        """Obtener solicitud activa del usuario (como pasajero o conductor)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Buscar como pasajero
                cursor = await db.execute("""
                    SELECT request_id, passenger_id, driver_id, pickup_zone, destination_zone,
                           estimated_cost, vehicle_type, status, created_at, special_instructions,
                           pickup_x, pickup_y, destination_x, destination_y
                    FROM taxi_requests 
                    WHERE (passenger_id = ? OR driver_id = ?) 
                    AND status IN ('pending', 'accepted', 'in_progress')
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id, user_id))
                
                row = await cursor.fetchone()
                if row:
                    return {
                        'request_id': row[0],
                        'passenger_id': row[1],
                        'driver_id': row[2],
                        'pickup_zone': row[3],
                        'destination_zone': row[4],
                        'estimated_cost': row[5],
                        'vehicle_type': row[6],
                        'status': row[7],
                        'created_at': row[8],
                        'special_instructions': row[9],
                        'pickup_x': row[10],
                        'pickup_y': row[11],
                        'destination_x': row[12],
                        'destination_y': row[13]
                    }
                return None
                
            except Exception as e:
                logger.error(f"Error obteniendo solicitud activa: {e}")
                return None

    async def accept_request(self, request_id: int, driver_user_id: int) -> Tuple[bool, str]:
        """Aceptar una solicitud de taxi por parte de un conductor"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Verificar que la solicitud esté pendiente y obtener el tipo de vehículo requerido
                cursor = await db.execute(
                    "SELECT status, vehicle_type FROM taxi_requests WHERE request_id = ?",
                    (request_id,)
                )
                
                row = await cursor.fetchone()
                if not row or row[0] != 'pending':
                    logger.warning(f"Solicitud {request_id} no está disponible para aceptar")
                    return False, "La solicitud no está disponible para aceptar"
                
                required_vehicle = row[1]
                
                # Verificar que el conductor existe y está disponible
                cursor = await db.execute(
                    "SELECT driver_id, vehicle_type FROM taxi_drivers WHERE user_id = ? AND status IN ('available', 'online')",
                    (driver_user_id,)
                )
                
                driver_row = await cursor.fetchone()
                if not driver_row:
                    logger.warning(f"Conductor {driver_user_id} no está disponible")
                    return False, "El conductor no está disponible"
                
                driver_id = driver_row[0]
                driver_vehicles_raw = driver_row[1]
                
                # Validar que el conductor tenga el vehículo necesario
                driver_vehicles = []
                if driver_vehicles_raw:
                    try:
                        import json
                        # Intentar parsear como JSON (múltiples vehículos)
                        driver_vehicles = json.loads(driver_vehicles_raw)
                    except:
                        # Si falla, es formato antiguo (un solo vehículo)
                        driver_vehicles = [driver_vehicles_raw]
                
                if required_vehicle not in driver_vehicles:
                    vehicle_names = {
                        'auto': 'Automóvil',
                        'sedan': 'Sedán',
                        'suv': 'SUV',
                        'pickup': 'Pickup',
                        'moto': 'Motocicleta',
                        'avion': 'Avión',
                        'barco': 'Barco'
                    }
                    required_name = vehicle_names.get(required_vehicle, required_vehicle)
                    logger.warning(f"Conductor {driver_user_id} no tiene vehículo requerido: {required_vehicle}")
                    return False, f"No tienes registrado el vehículo requerido: {required_name}"
                
                # Actualizar la solicitud con el conductor asignado
                await db.execute(
                    """UPDATE taxi_requests 
                       SET driver_id = ?, status = 'accepted', accepted_at = CURRENT_TIMESTAMP 
                       WHERE request_id = ? AND status = 'pending'""",
                    (driver_id, request_id)
                )
                
                # Verificar que se actualizó correctamente
                if db.total_changes > 0:
                    await db.commit()
                    logger.info(f"✅ Solicitud {request_id} aceptada por conductor {driver_user_id}")
                    return True, "Solicitud aceptada exitosamente"
                else:
                    logger.warning(f"No se pudo actualizar solicitud {request_id}")
                    return False, "Error interno al aceptar la solicitud"
                
            except Exception as e:
                logger.error(f"Error aceptando solicitud {request_id}: {e}")
                return False, f"Error: {str(e)}"

    async def cancel_request(self, request_id: int) -> Tuple[bool, str]:
        """Cancelar una solicitud de taxi (actualiza estado a 'cancelled' y registra fecha)"""
        import datetime
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cancelled_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                await db.execute("""
                    UPDATE taxi_requests
                    SET status = 'cancelled', cancelled_at = ?
                    WHERE request_id = ?
                """, (cancelled_at, request_id))
                await db.commit()
                logger.info(f"Solicitud {request_id} cancelada correctamente.")
                return True, "Solicitud cancelada correctamente."
            except Exception as e:
                logger.error(f"Error al cancelar solicitud {request_id}: {e}")
                return False, f"Error al cancelar solicitud: {str(e)}"

    async def validate_route(self, pickup_zone, destination_zone, vehicle_type: str) -> Tuple[bool, str]:
        """Validar si una ruta es válida según el tipo de vehículo"""
        try:
            from taxi_config import taxi_config
            import json
            
            # Obtener información del vehículo
            vehicle_info = taxi_config.VEHICLE_TYPES.get(vehicle_type)
            if not vehicle_info:
                return False, f"Tipo de vehículo no válido: {vehicle_type}"
            
            # Función para extraer información de zona (manejar tanto strings como dicts)
            def extract_zone_info(zone_data):
                if isinstance(zone_data, str):
                    try:
                        # Intentar parsear como JSON
                        zone_dict = json.loads(zone_data.replace("'", '"'))
                        return zone_dict.get('zone_name', zone_data), zone_dict.get('zone_id', '')
                    except:
                        # Si no es JSON, usar como string normal
                        return zone_data, ''
                elif isinstance(zone_data, dict):
                    return zone_data.get('zone_name', str(zone_data)), zone_data.get('zone_id', '')
                else:
                    return str(zone_data), ''
            
            # Extraer nombres de zona
            pickup_name, pickup_id = extract_zone_info(pickup_zone)
            destination_name, destination_id = extract_zone_info(destination_zone)
            
            logger.info(f"🔍 DATOS EXTRAÍDOS - Origen: '{pickup_name}' (ID: {pickup_id})")
            logger.info(f"🔍 DATOS EXTRAÍDOS - Destino: '{destination_name}' (ID: {destination_id})")
            
            # Función para verificar si una zona es de aeropuerto/pista
            def is_airport_zone(zone_name: str, zone_id: str = '') -> bool:
                logger.info(f"🔍 BUSCANDO ZONA AEROPORTUARIA: Nombre='{zone_name}', ID='{zone_id}'")
                
                # Verificar por zone_id primero (más confiable)
                if zone_id:
                    # IDs conocidos de aeropuertos
                    airport_ids = ['airport_b4_pad1', 'stop_z0_airstrip', 'stop_a4_airstrip', 'stop_a0_airstrip']
                    if any(airport_id in zone_id for airport_id in airport_ids):
                        logger.info(f"🛬 ENCONTRADO POR ZONE_ID: '{zone_id}' es un aeropuerto")
                        return True
                
                # Buscar en TAXI_STOPS por tipos aeroportuarios
                for stop_id, stop_data in taxi_config.TAXI_STOPS.items():
                    if stop_data['name'] == zone_name or stop_id == zone_id:
                        is_airport = stop_data['type'] in ['airport_stop', 'airstrip']
                        logger.info(f"🛬 ENCONTRADO EN TAXI_STOPS: {stop_id} - Nombre: '{stop_data['name']}' - Tipo: '{stop_data['type']}' - Es aeropuerto: {is_airport}")
                        return is_airport
                
                # Buscar en PVP_ZONES por tipos aeroportuarios
                for zone_key, zone_data in taxi_config.PVP_ZONES.items():
                    if zone_data['name'] == zone_name or zone_key == zone_id:
                        is_airport = zone_data['type'] in ['airport', 'airstrip']
                        logger.info(f"🛬 ENCONTRADO EN PVP_ZONES: {zone_key} - Nombre: '{zone_data['name']}' - Tipo: '{zone_data['type']}' - Es aeropuerto: {is_airport}")
                        return is_airport
                
                # Verificar por palabras clave en el nombre
                airport_keywords = ["Aeropuerto", "Pista de Aterrizaje", "Airport", "Airstrip"]
                keyword_match = any(keyword in zone_name for keyword in airport_keywords)
                if keyword_match:
                    logger.info(f"🛬 ENCONTRADO POR PALABRAS CLAVE: '{zone_name}' contiene palabras de aeropuerto")
                    return True
                
                # Verificar por coordenadas conocidas de aeropuertos
                airport_coords = ["Z0-8", "A4-3", "B4-1", "A0-1"]
                coord_match = any(coord in zone_name for coord in airport_coords)
                if coord_match:
                    logger.info(f"🛬 ENCONTRADO POR COORDENADAS: '{zone_name}' contiene coordenadas de aeropuerto")
                    return True
                
                logger.warning(f"❌ ZONA NO RECONOCIDA COMO AEROPUERTO: Nombre='{zone_name}', ID='{zone_id}'")
                return False
            
            # Función para verificar si una zona es de agua/puerto
            def is_water_zone(zone_name: str) -> bool:
                # Buscar en TAXI_STOPS por tipos acuáticos
                for stop_id, stop_data in taxi_config.TAXI_STOPS.items():
                    if stop_data['name'] == zone_name:
                        access_types = stop_data.get('access_types', [])
                        return any(water_type in access_types for water_type in ['water', 'port', 'seaplane'])
                
                # Buscar en PVP_ZONES por tipos acuáticos
                for zone_id, zone_data in taxi_config.PVP_ZONES.items():
                    if zone_data['name'] == zone_name:
                        access_types = zone_data.get('access_types', [])
                        return any(water_type in access_types for water_type in ['water', 'port', 'seaplane'])
                
                # Verificar por palabras clave en el nombre
                water_keywords = ["Puerto", "Marina", "Isla", "Muelle", "Barco"]
                return any(keyword in zone_name for keyword in water_keywords)
            
            # Función para verificar si una zona es una isla
            def is_island_zone(zone_name: str) -> bool:
                island_keywords = ["Isla", "Remote", "Island"]
                return any(keyword in zone_name for keyword in island_keywords)
            
            # NUEVA VALIDACIÓN: Usar la configuración de zonas en lugar de lógica hardcodeada
            pickup_valid = self.validate_vehicle_zone_access(pickup_name, pickup_id, vehicle_type)
            destination_valid = self.validate_vehicle_zone_access(destination_name, destination_id, vehicle_type)
            
            logger.info(f"🔍 VALIDACIÓN {vehicle_type.upper()} - Ruta: '{pickup_name}' -> '{destination_name}'")
            logger.info(f"🔍 VALIDACIÓN {vehicle_type.upper()} - Pickup válido: {pickup_valid}")
            logger.info(f"🔍 VALIDACIÓN {vehicle_type.upper()} - Destino válido: {destination_valid}")
            
            if not pickup_valid:
                return False, f"El {vehicle_info['name']} no puede acceder a '{pickup_name}'"
            
            if not destination_valid:
                return False, f"El {vehicle_info['name']} no puede acceder a '{destination_name}'"
            
            return True, "Ruta válida"
            
        except Exception as e:
            logger.error(f"Error validando ruta: {e}")
            return False, f"Error validando ruta: {str(e)}"

    def validate_vehicle_zone_access(self, zone_name: str, zone_id: str, vehicle_type: str) -> bool:
        """Validar si un vehículo puede acceder a una zona específica usando la configuración"""
        try:
            from taxi_config import taxi_config
            
            # Buscar la zona en TAXI_STOPS
            for stop_id, stop_data in taxi_config.TAXI_STOPS.items():
                if stop_data['name'] == zone_name or stop_id == zone_id:
                    vehicle_types = stop_data.get('vehicle_types', [])
                    return vehicle_type in vehicle_types or vehicle_type.title() in vehicle_types
            
            # Buscar la zona en PVP_ZONES
            for pvp_id, pvp_data in taxi_config.PVP_ZONES.items():
                if pvp_data['name'] == zone_name or pvp_id == zone_id:
                    vehicle_access = pvp_data.get('vehicle_access', [])
                    access_types = pvp_data.get('access_types', [])
                    
                    # Verificar si el vehículo está explícitamente permitido
                    if vehicle_type in vehicle_access or vehicle_type.title() in vehicle_access:
                        return True
                    
                    # Verificar compatibilidad por tipo de acceso
                    vehicle_info = taxi_config.VEHICLE_TYPES.get(vehicle_type, {})
                    vehicle_access_types = vehicle_info.get('access_types', [])
                    
                    # Verificar si hay compatibilidad de acceso
                    return any(access in vehicle_access_types for access in access_types)
            
            # Si no se encuentra la zona, permitir acceso (zona por defecto)
            logger.warning(f"⚠️ Zona no encontrada en configuración: {zone_name} (ID: {zone_id}) - Permitiendo acceso")
            return True
            
        except Exception as e:
            logger.error(f"Error validando acceso de vehículo: {e}")
            return True  # En caso de error, permitir acceso

    async def update_driver_vehicles(self, user_id: int, vehicles: List[str]) -> Tuple[bool, str]:
        """Actualizar vehículos del conductor (no sobrescribir, sino agregar/actualizar)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Verificar si es conductor
                cursor = await db.execute(
                    "SELECT driver_id FROM taxi_drivers WHERE user_id = ?",
                    (user_id,)
                )
                driver_row = await cursor.fetchone()
                
                if not driver_row:
                    return False, "No estás registrado como conductor"
                
                # Convertir lista de vehículos a string (JSON)
                import json
                vehicles_json = json.dumps(vehicles)
                
                # Actualizar vehículos
                await db.execute("""
                    UPDATE taxi_drivers 
                    SET vehicle_type = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (vehicles_json, user_id))
                
                await db.commit()
                return True, "Vehículos actualizados exitosamente"
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error actualizando vehículos: {e}")
                return False, str(e)

    async def get_user_by_id(self, user_id: int) -> dict:
        """Obtener datos de usuario por ID interno"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute("""
                    SELECT user_id, discord_id, discord_guild_id, username, 
                           display_name, created_at, last_active
                    FROM taxi_users 
                    WHERE user_id = ?
                """, (user_id,))
                
                row = await cursor.fetchone()
                if row:
                    return {
                        'user_id': row[0],
                        'discord_id': row[1],
                        'discord_guild_id': row[2],
                        'username': row[3],
                        'display_name': row[4],
                        'created_at': row[5],
                        'last_active': row[6]
                    }
                return None
                
            except Exception as e:
                logger.error(f"Error obteniendo usuario por ID: {e}")
                return None

    async def update_driver_status(self, discord_user_id: int, new_status: str) -> Tuple[bool, str]:
        """Actualizar el estado de un conductor usando su Discord ID"""
        valid_statuses = ['available', 'busy', 'offline', 'break']
        
        if new_status not in valid_statuses:
            return False, f"Estado inválido. Estados válidos: {', '.join(valid_statuses)}"
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Primero obtener el user_id interno usando el discord_id (NO discord_user_id)
                cursor = await db.execute("""
                    SELECT tu.user_id 
                    FROM taxi_users tu
                    WHERE tu.discord_id = ?
                """, (str(discord_user_id),))
                user_data = await cursor.fetchone()
                
                if not user_data:
                    return False, "Usuario no encontrado en el sistema"
                
                user_id = user_data[0]
                
                # Verificar que el conductor existe
                cursor = await db.execute(
                    "SELECT driver_id FROM taxi_drivers WHERE user_id = ?",
                    (user_id,)
                )
                driver = await cursor.fetchone()
                
                if not driver:
                    return False, "No se encontró el conductor en la base de datos"
                
                # Actualizar el estado
                await db.execute("""
                    UPDATE taxi_drivers 
                    SET status = ?, last_activity = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (new_status, user_id))
                
                await db.commit()
                logger.info(f"✅ Estado del conductor {discord_user_id} actualizado a: {new_status}")
                return True, f"Estado actualizado a {new_status}"
                
            except Exception as e:
                logger.error(f"❌ Error actualizando estado del conductor: {e}")
                return False, f"Error actualizando estado: {str(e)}"

    async def get_last_daily_claim(self, user_id: int) -> str:
        """Obtener la fecha del último canje diario del usuario"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT claimed_at FROM daily_rewards 
                    WHERE user_id = ? 
                    ORDER BY claimed_at DESC 
                    LIMIT 1
                """, (user_id,))
                
                result = await cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo último canje diario: {e}")
            return None

    async def add_daily_reward(self, user_id: int, amount: float = 500.0) -> bool:
        """Agregar recompensa diaria al usuario"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Registrar la recompensa
                await db.execute("""
                    INSERT INTO daily_rewards (user_id, amount)
                    VALUES (?, ?)
                """, (user_id, amount))
                
                # Actualizar el balance del usuario
                await db.execute("""
                    UPDATE bank_accounts 
                    SET balance = balance + ?, last_transaction = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (amount, user_id))
                
                # También actualizar last_active en taxi_users
                await db.execute("""
                    UPDATE taxi_users 
                    SET last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                
                await db.commit()
                logger.info(f"✅ Recompensa diaria de ${amount} agregada al usuario {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error agregando recompensa diaria: {e}")
            return False

    async def get_pack_stock(self, pack_id: str, tier: str, guild_id: str) -> int:
        """Obtener stock disponible de un pack en el servidor"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT current_stock FROM shop_stock 
                    WHERE pack_id = ? AND tier = ?
                """, (pack_id, tier))
                
                result = await cursor.fetchone()
                if result:
                    return result[0]
                else:
                    # Si no existe entrada, inicializar con stock por defecto
                    from shop_config import SHOP_PACKS
                    default_stock = SHOP_PACKS.get(tier, {}).get(pack_id, {}).get('stock', 5)
                    
                    await db.execute("""
                        INSERT INTO shop_stock (pack_id, tier, current_stock, max_stock)
                        VALUES (?, ?, ?, ?)
                    """, (pack_id, tier, default_stock, default_stock))
                    await db.commit()
                    return default_stock
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo stock del pack: {e}")
            return 0

    async def check_tier_cooldown(self, user_id: int, tier: str) -> tuple[bool, str]:
        """Verificar si el usuario puede comprar en este tier"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT next_available FROM shop_cooldowns 
                    WHERE user_id = ? AND tier = ?
                """, (user_id, tier))
                
                result = await cursor.fetchone()
                if not result:
                    # Primera compra, sin cooldown
                    return True, ""
                
                from datetime import datetime
                next_available = datetime.fromisoformat(result[0])
                now = datetime.now()
                
                if now >= next_available:
                    return True, ""
                else:
                    # En cooldown
                    timestamp = int(next_available.timestamp())
                    return False, f"<t:{timestamp}:R>"
                    
        except Exception as e:
            logger.error(f"❌ Error verificando cooldown: {e}")
            return False, "Error del sistema"

    async def process_pack_purchase(self, user_id: int, pack_id: str, tier: str, price: float, guild_id: str) -> bool:
        """Procesar la compra completa de un pack"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Verificar stock una vez más (race condition protection)
                cursor = await db.execute("""
                    SELECT current_stock FROM shop_stock 
                    WHERE pack_id = ? AND tier = ?
                """, (pack_id, tier))
                
                result = await cursor.fetchone()
                if not result or result[0] <= 0:
                    return False
                
                # Verificar saldo del usuario una vez más
                cursor = await db.execute("""
                    SELECT ba.balance 
                    FROM taxi_users tu
                    LEFT JOIN bank_accounts ba ON tu.user_id = ba.user_id
                    WHERE tu.user_id = ?
                """, (user_id,))
                
                user_result = await cursor.fetchone()
                if not user_result or not user_result[0] or user_result[0] < price:
                    return False
                
                # === TRANSACCIÓN ATÓMICA ===
                
                # 1. Debitar dinero del usuario
                await db.execute("""
                    UPDATE bank_accounts 
                    SET balance = balance - ?, last_transaction = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (price, user_id))
                
                # También actualizar last_active en taxi_users
                await db.execute("""
                    UPDATE taxi_users 
                    SET last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                
                # 2. Reducir stock
                # Primero verificar que la entrada existe
                cursor = await db.execute("""
                    SELECT current_stock FROM shop_stock 
                    WHERE pack_id = ? AND tier = ?
                """, (pack_id, tier))
                
                existing_stock = await cursor.fetchone()
                if not existing_stock:
                    # La entrada no existe, inicializarla primero
                    from shop_config import SHOP_PACKS
                    default_stock = SHOP_PACKS.get(tier, {}).get(pack_id, {}).get('stock', 5)
                    
                    await db.execute("""
                        INSERT INTO shop_stock (pack_id, tier, current_stock, max_stock)
                        VALUES (?, ?, ?, ?)
                    """, (pack_id, tier, default_stock, default_stock))
                    logger.info(f"✅ Stock inicializado para {pack_id} ({tier}): {default_stock}")
                
                # Ahora reducir stock
                rows_affected = await db.execute("""
                    UPDATE shop_stock 
                    SET current_stock = current_stock - 1
                    WHERE pack_id = ? AND tier = ?
                """, (pack_id, tier))
                
                # Verificar que se actualizó
                cursor = await db.execute("""
                    SELECT current_stock FROM shop_stock 
                    WHERE pack_id = ? AND tier = ?
                """, (pack_id, tier))
                
                new_stock = await cursor.fetchone()
                logger.info(f"✅ Stock actualizado para {pack_id} ({tier}): {new_stock[0] if new_stock else 'ERROR'}")
                
                # 3. Registrar la compra
                cursor = await db.execute("""
                    INSERT INTO shop_purchases 
                    (user_id, pack_id, tier, amount_paid, payment_method, purchased_at, status, guild_id)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                """, (user_id, pack_id, tier, price, 'money', 'pending', guild_id))
                
                purchase_id = cursor.lastrowid
                
                # 4. Actualizar/crear cooldown
                from datetime import datetime, timedelta
                from shop_config import TIER_CONFIG
                
                cooldown_days = TIER_CONFIG[tier]['cooldown_days']
                next_available = datetime.now() + timedelta(days=cooldown_days)
                
                await db.execute("""
                    INSERT OR REPLACE INTO shop_cooldowns 
                    (user_id, tier, last_purchase, next_available)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                """, (user_id, tier, next_available.isoformat()))
                
                await db.commit()
                logger.info(f"✅ Compra procesada exitosamente: Usuario {user_id}, Pack {pack_id}, Precio ${price}")
                return purchase_id
                
        except Exception as e:
            logger.error(f"❌ Error procesando compra del pack: {e}")
            return False

    async def initialize_shop_stock(self, guild_id: str):
        """Inicializar stock de la tienda para un servidor"""
        try:
            from shop_config import SHOP_PACKS
            
            async with aiosqlite.connect(self.db_path) as db:
                for tier, packs in SHOP_PACKS.items():
                    for pack_id, pack_data in packs.items():
                        # Verificar si ya existe
                        cursor = await db.execute("""
                            SELECT stock_id FROM shop_stock 
                            WHERE pack_id = ? AND tier = ?
                        """, (pack_id, tier))
                        
                        if not await cursor.fetchone():
                            # No existe, crear entrada
                            stock = pack_data.get('stock', 5)
                            await db.execute("""
                                INSERT INTO shop_stock 
                                (pack_id, tier, current_stock, max_stock)
                                VALUES (?, ?, ?, ?)
                            """, (pack_id, tier, stock, stock))
                
                await db.commit()
                logger.info(f"✅ Stock de tienda inicializado para servidor {guild_id}")
                
        except Exception as e:
            logger.error(f"❌ Error inicializando stock de tienda: {e}")

    async def get_all_shop_stock(self) -> list:
        """Obtener todo el stock actual para debugging"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT pack_id, tier, current_stock, max_stock 
                    FROM shop_stock 
                    ORDER BY tier, pack_id
                """)
                
                rows = await cursor.fetchall()
                return [
                    {
                        'pack_id': row[0],
                        'tier': row[1], 
                        'current_stock': row[2],
                        'max_stock': row[3]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo stock completo: {e}")
            return []

    async def mark_package_delivered(self, purchase_id: int, admin_discord_id: str) -> bool:
        """Marcar un paquete como entregado"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE shop_purchases 
                    SET status = 'delivered', 
                        delivered_at = CURRENT_TIMESTAMP,
                        delivered_by = ?
                    WHERE purchase_id = ?
                """, (admin_discord_id, purchase_id))
                
                await db.commit()
                logger.info(f"✅ Paquete {purchase_id} marcado como entregado por {admin_discord_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error marcando paquete como entregado: {e}")
            return False

    async def get_pending_packages(self, guild_id: str) -> list:
        """Obtener lista de paquetes pendientes de entrega"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT sp.purchase_id, sp.pack_id, sp.tier, sp.amount_paid, 
                           sp.purchased_at, tu.discord_id, tu.display_name
                    FROM shop_purchases sp
                    JOIN taxi_users tu ON sp.user_id = tu.user_id
                    WHERE sp.status = 'pending' AND sp.guild_id = ?
                    ORDER BY sp.purchased_at ASC
                """, (guild_id,))
                
                rows = await cursor.fetchall()
                return [
                    {
                        'purchase_id': row[0],
                        'pack_id': row[1],
                        'tier': row[2],
                        'amount_paid': row[3],
                        'purchased_at': row[4],
                        'user_discord_id': row[5],
                        'user_display_name': row[6]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo paquetes pendientes: {e}")
            return []

    async def get_purchase_details(self, purchase_id: int) -> dict:
        """Obtener detalles de una compra específica"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT sp.*, tu.discord_id, tu.display_name
                    FROM shop_purchases sp
                    JOIN taxi_users tu ON sp.user_id = tu.user_id
                    WHERE sp.purchase_id = ?
                """, (purchase_id,))
                
                row = await cursor.fetchone()
                if not row:
                    return None
                
                return {
                    'purchase_id': row[0],
                    'user_id': row[1], 
                    'pack_id': row[2],
                    'tier': row[3],
                    'amount_paid': row[4],
                    'payment_method': row[5],
                    'payment_details': row[6],
                    'purchased_at': row[7],
                    'status': row[8],
                    'delivered_at': row[9],
                    'delivered_by': row[10],
                    'guild_id': row[11],
                    'user_discord_id': row[12],
                    'user_display_name': row[13]
                }
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo detalles de compra: {e}")
            return None

    # === SISTEMA DE ALERTAS DE REINICIO ===
    
    async def add_reset_schedule(self, server_name: str, reset_time: str, admin_id: str, 
                               timezone: str = 'UTC', days_of_week: str = '1,2,3,4,5,6,7') -> bool:
        """Agregar un horario de reinicio para un servidor"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO reset_schedules (server_name, reset_time, timezone, days_of_week, created_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (server_name, reset_time, timezone, days_of_week, admin_id))
                
                await db.commit()
                logger.info(f"✅ Horario de reinicio agregado para {server_name}: {reset_time}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error agregando horario de reinicio: {e}")
            return False

    async def remove_reset_schedule(self, schedule_id: int) -> bool:
        """Eliminar un horario de reinicio"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM reset_schedules WHERE id = ?", (schedule_id,))
                await db.commit()
                logger.info(f"✅ Horario de reinicio {schedule_id} eliminado")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error eliminando horario de reinicio: {e}")
            return False

    async def get_reset_schedules(self, server_name: str = None) -> list:
        """Obtener horarios de reinicio"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if server_name:
                    cursor = await db.execute("""
                        SELECT id, server_name, reset_time, timezone, days_of_week, created_at, created_by, active
                        FROM reset_schedules 
                        WHERE server_name = ? AND active = 1
                        ORDER BY reset_time
                    """, (server_name,))
                else:
                    cursor = await db.execute("""
                        SELECT id, server_name, reset_time, timezone, days_of_week, created_at, created_by, active
                        FROM reset_schedules 
                        WHERE active = 1
                        ORDER BY server_name, reset_time
                    """)
                
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row[0],
                        'server_name': row[1],
                        'reset_time': row[2],
                        'timezone': row[3],
                        'days_of_week': row[4],
                        'created_at': row[5],
                        'created_by': row[6],
                        'active': row[7]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo horarios de reinicio: {e}")
            return []

    async def subscribe_to_reset_alerts(self, user_id: str, guild_id: str, server_name: str, 
                                      minutes_before: int = 15) -> bool:
        """Suscribir usuario a alertas de reinicio"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO user_reset_alerts 
                    (user_id, guild_id, server_name, alert_enabled, minutes_before)
                    VALUES (?, ?, ?, 1, ?)
                """, (user_id, guild_id, server_name, minutes_before))
                
                await db.commit()
                logger.info(f"✅ Usuario {user_id} suscrito a alertas de {server_name}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error suscribiendo a alertas: {e}")
            return False

    async def unsubscribe_from_reset_alerts(self, user_id: str, guild_id: str, server_name: str) -> bool:
        """Desuscribir usuario de alertas de reinicio"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE user_reset_alerts 
                    SET alert_enabled = 0
                    WHERE user_id = ? AND guild_id = ? AND server_name = ?
                """, (user_id, guild_id, server_name))
                
                await db.commit()
                logger.info(f"✅ Usuario {user_id} desuscrito de alertas de {server_name}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error desuscribiendo de alertas: {e}")
            return False

    async def get_users_for_reset_alert(self, server_name: str) -> list:
        """Obtener usuarios suscritos a alertas de un servidor específico"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT user_id, guild_id, minutes_before
                    FROM user_reset_alerts 
                    WHERE server_name = ? AND alert_enabled = 1
                """, (server_name,))
                
                rows = await cursor.fetchall()
                return [
                    {
                        'user_id': row[0],
                        'guild_id': row[1],
                        'minutes_before': row[2]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo usuarios para alertas: {e}")
            return []

    async def get_user_reset_subscriptions(self, user_id: str, guild_id: str) -> list:
        """Obtener suscripciones de alertas de un usuario"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT server_name, alert_enabled, minutes_before, created_at
                    FROM user_reset_alerts 
                    WHERE user_id = ? AND guild_id = ?
                """, (user_id, guild_id))
                
                rows = await cursor.fetchall()
                return [
                    {
                        'server_name': row[0],
                        'alert_enabled': row[1],
                        'minutes_before': row[2],
                        'created_at': row[3]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo suscripciones del usuario: {e}")
            return []

    async def check_alert_already_sent(self, user_id: str, guild_id: str, server_name: str, 
                                     schedule_id: int, alert_date: str) -> bool:
        """Verificar si ya se envió una alerta para este día"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM reset_alert_cache 
                    WHERE user_id = ? AND guild_id = ? AND server_name = ? 
                    AND schedule_id = ? AND alert_date = ?
                """, (user_id, guild_id, server_name, schedule_id, alert_date))
                
                count = await cursor.fetchone()
                return count[0] > 0
                
        except Exception as e:
            logger.error(f"❌ Error verificando caché de alerta: {e}")
            return False

    async def mark_alert_sent(self, user_id: str, guild_id: str, server_name: str, 
                            schedule_id: int, alert_date: str) -> bool:
        """Marcar alerta como enviada en el caché"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR IGNORE INTO reset_alert_cache 
                    (user_id, guild_id, server_name, schedule_id, alert_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, guild_id, server_name, schedule_id, alert_date))
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Error marcando alerta como enviada: {e}")
            return False

    async def cleanup_old_alert_cache(self, days_old: int = 7) -> bool:
        """Limpiar caché de alertas antiguas"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d')
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    DELETE FROM reset_alert_cache 
                    WHERE alert_date < ?
                """, (cutoff_date,))
                
                await db.commit()
                logger.info(f"✅ Caché de alertas limpiado (eliminadas alertas anteriores a {cutoff_date})")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error limpiando caché de alertas: {e}")
            return False

    async def get_active_trips_for_driver(self, driver_id: int) -> list:
        """Obtener viajes activos para un conductor específico"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT tr.request_id, tr.passenger_id, tr.pickup_zone, tr.destination_zone,
                           tr.estimated_cost, tr.final_cost, tr.created_at, tr.driver_accepted_at,
                           tu.discord_id as passenger_discord_id, tu.display_name as passenger_name
                    FROM taxi_requests tr
                    JOIN taxi_users tu ON tr.passenger_id = tu.user_id
                    WHERE tr.driver_id = ? AND tr.status = 'accepted'
                    ORDER BY tr.driver_accepted_at DESC
                """, (driver_id,))
                
                rows = await cursor.fetchall()
                
                trips = []
                for row in rows:
                    trips.append({
                        'request_id': row[0],
                        'passenger_id': row[1],
                        'pickup_zone': row[2],
                        'destination_zone': row[3],
                        'estimated_cost': row[4],
                        'final_cost': row[5],
                        'created_at': row[6],
                        'accepted_at': row[7],
                        'passenger_discord_id': row[8],
                        'passenger_name': row[9]
                    })
                
                return trips
                
        except Exception as e:
            logger.error(f"Error obteniendo viajes activos para conductor {driver_id}: {e}")
            return []

    async def complete_trip(self, request_id: int, driver_id: int, final_cost: float = None) -> tuple[bool, str]:
        """Completar un viaje y actualizar estadísticas"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Verificar que el viaje existe y está aceptado por este conductor
                cursor = await db.execute("""
                    SELECT tr.request_id, tr.passenger_id, tr.estimated_cost, tr.driver_id, tr.status,
                           td.user_id as driver_user_id, td.total_rides, td.total_earnings
                    FROM taxi_requests tr
                    JOIN taxi_drivers td ON tr.driver_id = td.driver_id
                    WHERE tr.request_id = ? AND tr.driver_id = ? AND tr.status = 'accepted'
                """, (request_id, driver_id))
                
                trip_data = await cursor.fetchone()
                
                if not trip_data:
                    return False, "Viaje no encontrado o no está activo para este conductor"
                
                passenger_id = trip_data[1]
                estimated_cost = trip_data[2]
                driver_user_id = trip_data[5]
                current_total_rides = trip_data[6] or 0
                current_total_earnings = trip_data[7] or 0.0
                
                # Usar costo final o estimado
                cost_to_charge = final_cost if final_cost is not None else estimated_cost
                
                # Marcar viaje como completado
                await db.execute("""
                    UPDATE taxi_requests 
                    SET status = 'completed', 
                        final_cost = ?,
                        completed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE request_id = ?
                """, (cost_to_charge, request_id))
                
                # Actualizar estadísticas del conductor
                await db.execute("""
                    UPDATE taxi_drivers 
                    SET total_rides = ?,
                        total_earnings = ?,
                        earnings_today = earnings_today + ?,
                        last_activity = CURRENT_TIMESTAMP
                    WHERE driver_id = ?
                """, (current_total_rides + 1, current_total_earnings + cost_to_charge, cost_to_charge, driver_id))
                
                # Procesar pago si hay sistema bancario
                try:
                    # Obtener cuentas bancarias
                    cursor = await db.execute("""
                        SELECT ba.account_number FROM bank_accounts ba
                        JOIN taxi_users tu ON ba.user_id = tu.user_id
                        WHERE tu.user_id = ? LIMIT 1
                    """, (passenger_id,))
                    passenger_account = await cursor.fetchone()
                    
                    cursor = await db.execute("""
                        SELECT ba.account_number FROM bank_accounts ba
                        WHERE ba.user_id = ? LIMIT 1
                    """, (driver_user_id,))
                    driver_account = await cursor.fetchone()
                    
                    if passenger_account and driver_account:
                        passenger_account_num = passenger_account[0]
                        driver_account_num = driver_account[0]
                        
                        # Verificar balance del pasajero
                        cursor = await db.execute("""
                            SELECT balance FROM bank_accounts WHERE account_number = ?
                        """, (passenger_account_num,))
                        passenger_balance_row = await cursor.fetchone()
                        
                        if passenger_balance_row and passenger_balance_row[0] >= cost_to_charge:
                            # Transferir dinero
                            await db.execute("""
                                UPDATE bank_accounts SET balance = balance - ? 
                                WHERE account_number = ?
                            """, (cost_to_charge, passenger_account_num))
                            
                            await db.execute("""
                                UPDATE bank_accounts SET balance = balance + ? 
                                WHERE account_number = ?
                            """, (cost_to_charge, driver_account_num))
                            
                            # Registrar transacciones
                            from datetime import datetime
                            transaction_time = datetime.now().isoformat()
                            
                            await db.execute("""
                                INSERT INTO bank_transactions 
                                (from_account, to_account, amount, transaction_type, description, created_at)
                                VALUES (?, ?, ?, 'taxi_payment', ?, ?)
                            """, (passenger_account_num, driver_account_num, cost_to_charge, 
                                  f"Pago viaje taxi #{request_id}", transaction_time))
                            
                            logger.info(f"💰 Pago procesado: ${cost_to_charge:.2f} de {passenger_account_num} a {driver_account_num}")
                        else:
                            logger.warning(f"⚠️ Balance insuficiente para viaje #{request_id}")
                            
                except Exception as payment_error:
                    logger.warning(f"Error procesando pago para viaje #{request_id}: {payment_error}")
                    # No fallar la finalización por error de pago
                
                await db.commit()
                logger.info(f"✅ Viaje #{request_id} completado por conductor {driver_id}")
                return True, f"Viaje completado exitosamente. Ganancia: ${cost_to_charge:.2f}"
                
        except Exception as e:
            logger.error(f"Error completando viaje {request_id}: {e}")
            return False, f"Error completando viaje: {str(e)}"

    async def add_trip_rating(self, request_id: int, rater_user_id: int, rated_user_id: int, 
                             rating: int, comment: str = None, rating_type: str = "passenger_to_driver") -> tuple[bool, str]:
        """Agregar calificación a un viaje completado"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Verificar que el viaje está completado
                cursor = await db.execute("""
                    SELECT status FROM taxi_requests WHERE request_id = ?
                """, (request_id,))
                
                trip_status = await cursor.fetchone()
                if not trip_status or trip_status[0] != 'completed':
                    return False, "Solo se pueden calificar viajes completados"
                
                # Verificar si ya existe una calificación de este tipo
                cursor = await db.execute("""
                    SELECT rating_id FROM taxi_ratings 
                    WHERE request_id = ? AND rater_id = ? AND rating_type = ?
                """, (request_id, rater_user_id, rating_type))
                
                existing_rating = await cursor.fetchone()
                if existing_rating:
                    return False, "Ya has calificado este viaje"
                
                # Insertar calificación
                await db.execute("""
                    INSERT INTO taxi_ratings (request_id, rater_id, rated_id, rating, comment, rating_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (request_id, rater_user_id, rated_user_id, rating, comment, rating_type))
                
                # Actualizar rating promedio del conductor si es calificación hacia conductor
                if rating_type == "passenger_to_driver":
                    await self._update_driver_rating(rated_user_id)
                
                await db.commit()
                return True, "Calificación agregada exitosamente"
                
        except Exception as e:
            logger.error(f"Error agregando calificación: {e}")
            return False, f"Error agregando calificación: {str(e)}"

    async def _update_driver_rating(self, driver_user_id: int):
        """Actualizar rating promedio de un conductor"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Calcular rating promedio
                cursor = await db.execute("""
                    SELECT AVG(tr.rating) FROM taxi_ratings tr
                    JOIN taxi_requests treq ON tr.request_id = treq.request_id
                    JOIN taxi_drivers td ON treq.driver_id = td.driver_id
                    WHERE td.user_id = ? AND tr.rating_type = 'passenger_to_driver'
                """, (driver_user_id,))
                
                avg_rating = await cursor.fetchone()
                if avg_rating and avg_rating[0]:
                    new_rating = round(avg_rating[0], 2)
                    
                    # Actualizar rating del conductor
                    await db.execute("""
                        UPDATE taxi_drivers SET rating = ? WHERE user_id = ?
                    """, (new_rating, driver_user_id))
                    
                    logger.info(f"📊 Rating actualizado para conductor {driver_user_id}: {new_rating}")
                    
        except Exception as e:
            logger.error(f"Error actualizando rating del conductor: {e}")

    def get_driver_level_info(self, total_rides: int, rating: float) -> dict:
        """Obtener información del nivel del conductor basado en viajes y rating"""
        try:
            # Definir niveles basados en viajes completados
            level_thresholds = [
                {"min_rides": 0, "level": 1, "title": "Novato", "emoji": "🟫", "bonus": 0.0},
                {"min_rides": 5, "level": 2, "title": "Principiante", "emoji": "⚫", "bonus": 0.05},
                {"min_rides": 15, "level": 3, "title": "Conductor", "emoji": "🔵", "bonus": 0.10},
                {"min_rides": 30, "level": 4, "title": "Experimentado", "emoji": "🟢", "bonus": 0.15},
                {"min_rides": 50, "level": 5, "title": "Veterano", "emoji": "🟡", "bonus": 0.20},
                {"min_rides": 75, "level": 6, "title": "Experto", "emoji": "🟠", "bonus": 0.25},
                {"min_rides": 100, "level": 7, "title": "Maestro", "emoji": "🔴", "bonus": 0.30},
                {"min_rides": 150, "level": 8, "title": "Profesional", "emoji": "🟣", "bonus": 0.35},
                {"min_rides": 200, "level": 9, "title": "Elite", "emoji": "⚪", "bonus": 0.40},
                {"min_rides": 300, "level": 10, "title": "Leyenda", "emoji": "🟨", "bonus": 0.50}
            ]
            
            # Encontrar nivel actual
            current_level = level_thresholds[0]
            for threshold in level_thresholds:
                if total_rides >= threshold["min_rides"]:
                    current_level = threshold
                else:
                    break
            
            # Calcular progreso hacia el siguiente nivel
            next_level = None
            rides_to_next = None
            
            for threshold in level_thresholds:
                if threshold["level"] > current_level["level"]:
                    next_level = threshold
                    rides_to_next = threshold["min_rides"] - total_rides
                    break
            
            # Aplicar modificadores por rating
            rating_modifier = 1.0
            rating_description = "⭐ Estándar"
            
            if rating >= 4.8:
                rating_modifier = 1.2
                rating_description = "⭐⭐⭐ Excelencia"
            elif rating >= 4.5:
                rating_modifier = 1.15
                rating_description = "⭐⭐ Sobresaliente"
            elif rating >= 4.0:
                rating_modifier = 1.1
                rating_description = "⭐ Bueno"
            elif rating < 3.0:
                rating_modifier = 0.9
                rating_description = "❌ Necesita Mejorar"
            
            # Calcular bonus total
            base_bonus = current_level["bonus"]
            total_bonus = base_bonus * rating_modifier
            
            return {
                "level": current_level["level"],
                "title": current_level["title"],
                "emoji": current_level["emoji"],
                "base_bonus": base_bonus,
                "rating_modifier": rating_modifier,
                "total_bonus": total_bonus,
                "rating_description": rating_description,
                "total_rides": total_rides,
                "rating": rating,
                "next_level": next_level,
                "rides_to_next": rides_to_next,
                "display_name": f"{current_level['emoji']} {current_level['title']} Nivel {current_level['level']}"
            }
            
        except Exception as e:
            logger.error(f"Error calculando nivel del conductor: {e}")
            return {
                "level": 1, "title": "Novato", "emoji": "🟫", "base_bonus": 0.0,
                "rating_modifier": 1.0, "total_bonus": 0.0, "rating_description": "⭐ Estándar",
                "total_rides": total_rides, "rating": rating, "next_level": None, "rides_to_next": None,
                "display_name": "🟫 Novato Nivel 1"
            }

    async def get_leaderboard(self, guild_id: str, limit: int = 10) -> list:
        """Obtener tabla de clasificación de conductores"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT td.driver_id, td.total_rides, td.total_earnings, td.rating,
                           td.vehicle_type, tu.display_name, td.created_at
                    FROM taxi_drivers td
                    JOIN taxi_users tu ON td.user_id = tu.user_id
                    WHERE tu.discord_guild_id = ? AND td.total_rides > 0
                    ORDER BY td.total_rides DESC, td.rating DESC, td.total_earnings DESC
                    LIMIT ?
                """, (guild_id, limit))
                
                rows = await cursor.fetchall()
                
                leaderboard = []
                for i, row in enumerate(rows):
                    driver_id = row[0]
                    total_rides = row[1] or 0
                    total_earnings = row[2] or 0.0
                    rating = row[3] or 5.0
                    vehicle_type = row[4]
                    display_name = row[5]
                    created_at = row[6]
                    
                    level_info = self.get_driver_level_info(total_rides, rating)
                    
                    leaderboard.append({
                        "position": i + 1,
                        "driver_id": driver_id,
                        "display_name": display_name,
                        "level_info": level_info,
                        "total_rides": total_rides,
                        "total_earnings": total_earnings,
                        "rating": rating,
                        "vehicle_type": vehicle_type,
                        "avg_earnings": total_earnings / max(total_rides, 1)
                    })
                
                return leaderboard
                
        except Exception as e:
            logger.error(f"Error obteniendo leaderboard: {e}")
            return []

# Instancia global
taxi_db = TaxiDatabase()
