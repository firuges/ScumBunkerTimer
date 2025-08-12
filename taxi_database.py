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
            
            await db.commit()
            logger.info("✅ Base de datos del sistema de taxi inicializada")

    # === GESTIÓN DE USUARIOS ===
    
    async def register_user(self, discord_id: str, guild_id: str, username: str, display_name: str = None) -> Tuple[bool, Dict]:
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
                
                # Registrar usuario
                cursor = await db.execute("""
                    INSERT INTO taxi_users (discord_id, discord_guild_id, username, display_name, welcome_pack_claimed)
                    VALUES (?, ?, ?, ?, TRUE)
                """, (discord_id, guild_id, username, display_name))
                
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
                SELECT tu.*, ba.account_number, ba.balance
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
                "account_number": row[10],
                "balance": float(row[11]) if row[11] else 0.0
            }

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

    async def validate_route(self, pickup_zone: str, destination_zone: str, vehicle_type: str) -> Tuple[bool, str]:
        """Validar si una ruta es válida según el tipo de vehículo"""
        try:
            from taxi_config import taxi_config
            
            # Obtener información del vehículo
            vehicle_info = taxi_config.VEHICLE_TYPES.get(vehicle_type)
            if not vehicle_info:
                return False, f"Tipo de vehículo no válido: {vehicle_type}"
            
            # Definir zonas que requieren tipos específicos de transporte
            airport_zones = ["Aeropuerto Principal", "Pista de Aterrizaje Sur", "Aeropuerto Norte", "Z0-8", "A4-3", "B4-1", "A0-1"]
            water_zones = ["Puerto Este", "Puerto Oeste", "Marina", "Isla", "Muelle"]
            island_zones = ["Isla Sur Remote", "Isla Norte", "Isla Central"]
            
            # Validaciones específicas para aviones
            if vehicle_type == "avion":
                # Los aviones solo pueden ir entre aeropuertos/pistas
                pickup_is_airport = any(airport in pickup_zone for airport in airport_zones)
                destination_is_airport = any(airport in destination_zone for airport in airport_zones)
                
                if not (pickup_is_airport and destination_is_airport):
                    return False, "Los aviones solo pueden volar entre aeropuertos y pistas de aterrizaje"
            
            # Validaciones para barcos
            elif vehicle_type == "barco":
                # Los barcos necesitan al menos un extremo en agua/puerto
                pickup_is_water = any(water in pickup_zone for water in water_zones)
                destination_is_water = any(water in destination_zone for water in water_zones)
                pickup_is_island = any(island in pickup_zone for island in island_zones)
                destination_is_island = any(island in destination_zone for island in island_zones)
                
                if not (pickup_is_water or destination_is_water or pickup_is_island or destination_is_island):
                    return False, "Los barcos necesitan al menos un puerto, muelle o isla como origen o destino"
            
            # Validaciones para islas (solo barco o hidroavión)
            if any(island in pickup_zone for island in island_zones) or any(island in destination_zone for island in island_zones):
                if vehicle_type not in ["barco", "hidroavion"]:
                    return False, "Para llegar a las islas solo se puede usar barco o hidroavión"
            
            return True, "Ruta válida"
            
        except Exception as e:
            logger.error(f"Error validando ruta: {e}")
            return False, f"Error validando ruta: {str(e)}"

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
                    SELECT user_id, discord_user_id, discord_guild_id, username, 
                           display_name, created_at, last_activity
                    FROM taxi_users 
                    WHERE user_id = ?
                """, (user_id,))
                
                row = await cursor.fetchone()
                if row:
                    return {
                        'user_id': row[0],
                        'discord_user_id': row[1],
                        'discord_guild_id': row[2],
                        'username': row[3],
                        'display_name': row[4],
                        'created_at': row[5],
                        'last_activity': row[6]
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

# Instancia global
taxi_db = TaxiDatabase()
