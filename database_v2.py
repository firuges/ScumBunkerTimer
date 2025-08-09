#!/usr/bin/env python3
"""
Base de datos mejorada con soporte para múltiples servidores
"""

import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class BunkerDatabaseV2:
    def __init__(self, db_path: str = "bunkers_v2.db"):
        self.db_path = db_path

    async def initialize(self):
        """Inicializa la base de datos con soporte para servidores"""
        async with aiosqlite.connect(self.db_path) as db:
            # Crear tabla de servidores
            await db.execute("""
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_by TEXT,
                    discord_guild_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, discord_guild_id)
                )
            """)
            
            # Crear tabla de bunkers (modificada para incluir servidor)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bunkers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sector TEXT NOT NULL,
                    name TEXT NOT NULL,
                    server_name TEXT DEFAULT 'Default',
                    discord_guild_id TEXT NOT NULL,
                    registered_time TIMESTAMP,
                    expiry_time TIMESTAMP,
                    registered_by TEXT,
                    discord_user_id TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sector, server_name, discord_guild_id)
                )
            """)
            
            # Crear tabla de uso diario para plan gratuito
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_guild_id TEXT NOT NULL,
                    discord_user_id TEXT NOT NULL,
                    usage_date DATE NOT NULL,
                    bunkers_registered INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(discord_guild_id, discord_user_id, usage_date)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bunker_sector TEXT,
                    server_name TEXT DEFAULT 'Default',
                    discord_guild_id TEXT NOT NULL,
                    notification_time TIMESTAMP,
                    notification_type TEXT,
                    sent BOOLEAN DEFAULT FALSE,
                    registered_by_id TEXT
                )
            """)
            
            # Tabla para configuraciones de notificación
            await db.execute("""
                CREATE TABLE IF NOT EXISTS notification_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    server_name TEXT DEFAULT 'Default',
                    bunker_sector TEXT DEFAULT 'all_sectors',
                    notification_type TEXT DEFAULT 'all',
                    role_id TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    personal_dm BOOLEAN DEFAULT FALSE,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(discord_guild_id, channel_id, server_name, bunker_sector, notification_type)
                )
            """)
            
            # Insertar servidor por defecto (lo haremos dinámico)
            # await db.execute("""
            #     INSERT OR IGNORE INTO servers (name, description, created_by, discord_guild_id) 
            #     VALUES ('Default', 'Servidor por defecto', 'System', 'default')
            # """)
            
            # Los bunkers se crearán cuando se agregue el primer servidor
            # bunkers_data = [
            #     ("D1", "Bunker Abandonado D1"),
            #     ("C4", "Bunker Abandonado C4"),
            #     ("A1", "Bunker Abandonado A1"),
            #     ("A3", "Bunker Abandonado A3")
            # ]
            
            # for sector, name in bunkers_data:
            #     await db.execute("""
            #         INSERT OR IGNORE INTO bunkers (sector, name, server_name, discord_guild_id) 
            #         VALUES (?, ?, 'Default', 'default')
            #     """, (sector, name))
            
            await db.commit()
            logger.info("Base de datos V2 inicializada correctamente")

    # === GESTIÓN DE SERVIDORES ===
    
    async def add_server(self, name: str, description: str = "", created_by: str = "", guild_id: str = "") -> bool:
        """Agregar un nuevo servidor para un Discord guild específico"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO servers (name, description, created_by, discord_guild_id) 
                    VALUES (?, ?, ?, ?)
                """, (name, description, created_by, guild_id))
                
                # Crear bunkers para el nuevo servidor
                bunkers_data = [
                    ("D1", "Bunker Abandonado D1"),
                    ("C4", "Bunker Abandonado C4"),
                    ("A1", "Bunker Abandonado A1"),
                    ("A3", "Bunker Abandonado A3")
                ]
                
                for sector, bunker_name in bunkers_data:
                    await db.execute("""
                        INSERT INTO bunkers (sector, name, server_name, discord_guild_id) 
                        VALUES (?, ?, ?, ?)
                    """, (sector, bunker_name, name, guild_id))
                
                await db.commit()
                logger.info(f"Servidor '{name}' agregado correctamente")
                return True
                
        except Exception as e:
            logger.error(f"Error agregando servidor: {e}")
            return False

    async def remove_server(self, name: str, guild_id: str) -> bool:
        """Eliminar un servidor y todos sus bunkers de un Discord guild específico"""
        try:
            if name == 'Default':
                logger.warning("No se puede eliminar el servidor por defecto")
                return False
                
            async with aiosqlite.connect(self.db_path) as db:
                # Verificar si el servidor existe en este guild
                cursor = await db.execute("SELECT name FROM servers WHERE name = ? AND discord_guild_id = ?", (name, guild_id))
                if not await cursor.fetchone():
                    return False
                
                # Eliminar notificaciones del servidor en este guild
                await db.execute("DELETE FROM notifications WHERE server_name = ? AND discord_guild_id = ?", (name, guild_id))
                
                # Eliminar bunkers del servidor en este guild
                await db.execute("DELETE FROM bunkers WHERE server_name = ? AND discord_guild_id = ?", (name, guild_id))
                
                # Eliminar el servidor de este guild
                await db.execute("DELETE FROM servers WHERE name = ? AND discord_guild_id = ?", (name, guild_id))
                
                await db.commit()
                logger.info(f"Servidor '{name}' eliminado correctamente")
                return True
                
        except Exception as e:
            logger.error(f"Error eliminando servidor: {e}")
            return False

    async def get_servers(self, guild_id: str) -> List[Dict]:
        """Obtener lista de servidores de un Discord guild específico"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT name, description, created_by, created_at 
                FROM servers WHERE discord_guild_id = ? ORDER BY name
            """, (guild_id,))
            
            servers = []
            async for row in cursor:
                servers.append({
                    "name": row[0],
                    "description": row[1],
                    "created_by": row[2],
                    "created_at": row[3]
                })
            
            return servers

    # === GESTIÓN DE BUNKERS (MODIFICADA) ===
    
    async def register_bunker_time(self, sector: str, hours: int, minutes: int, 
                                 registered_by: str, guild_id: str, discord_user_id: str = None, 
                                 server_name: str = "Default") -> bool:
        """Registra el tiempo de un bunker en un servidor específico de un Discord guild"""
        try:
            current_time = datetime.now()
            expiry_time = current_time + timedelta(hours=hours, minutes=minutes)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE bunkers 
                    SET registered_time = ?, expiry_time = ?, registered_by = ?, 
                        discord_user_id = ?, last_updated = ?
                    WHERE sector = ? AND server_name = ? AND discord_guild_id = ?
                """, (current_time, expiry_time, registered_by, discord_user_id, 
                      current_time, sector, server_name, guild_id))
                
                await db.commit()
                
                # Programar notificaciones
                await self._schedule_notifications(sector, expiry_time, server_name, guild_id)
                
                logger.info(f"Tiempo registrado para bunker {sector} en servidor {server_name}, guild {guild_id}: {hours}h {minutes}m")
                return True
                
        except Exception as e:
            logger.error(f"Error registrando tiempo: {e}")
            return False

    async def get_bunker_status(self, sector: str, guild_id: str, server_name: str = "Default") -> Optional[Dict]:
        """Obtiene el estado actual de un bunker en un servidor específico de un Discord guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT sector, name, registered_time, expiry_time, registered_by, discord_user_id, server_name
                FROM bunkers WHERE sector = ? AND server_name = ? AND discord_guild_id = ?
            """, (sector, server_name, guild_id))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            sector, name, registered_time, expiry_time, registered_by, discord_user_id, server_name = row
            
            result = {
                "sector": sector,
                "name": name,
                "registered_by": registered_by,
                "discord_user_id": discord_user_id,
                "server_name": server_name
            }
            
            if expiry_time:
                expiry_dt = datetime.fromisoformat(expiry_time)
                current_time = datetime.now()
                
                # Calcular diferencia de tiempo
                time_diff = expiry_dt - current_time
                
                if time_diff.total_seconds() > 0:
                    # ESTADO 1: CERRADO - Aún no llega a 0
                    result["status"] = "closed"
                    hours = int(time_diff.total_seconds() // 3600)
                    minutes = int((time_diff.total_seconds() % 3600) // 60)
                    result["time_remaining"] = f"{hours}h {minutes}m"
                    result["expiry_time"] = expiry_dt
                    result["status_text"] = "CERRADO"
                    
                elif time_diff.total_seconds() > -86400:  # -24 horas en segundos
                    # ESTADO 2: ACTIVO - Entre 0 y -24 horas (bunker abierto)
                    result["status"] = "active"
                    active_time = abs(time_diff.total_seconds())
                    active_hours = int(active_time // 3600)
                    active_minutes = int((active_time % 3600) // 60)
                    remaining_active_time = 86400 - active_time  # 24 horas - tiempo transcurrido
                    remaining_hours = int(remaining_active_time // 3600)
                    remaining_minutes = int((remaining_active_time % 3600) // 60)
                    
                    result["time_remaining"] = f"{remaining_hours}h {remaining_minutes}m"
                    result["active_since"] = f"{active_hours}h {active_minutes}m"
                    result["status_text"] = "ACTIVO"
                    
                    # Calcular cuándo expirará (24 horas después de abrirse)
                    final_expiry = expiry_dt + timedelta(hours=24)
                    result["final_expiry_time"] = final_expiry
                    
                else:
                    # ESTADO 3: EXPIRADO - Más de 24 horas después de abrirse
                    result["status"] = "expired"
                    total_expired_time = abs(time_diff.total_seconds()) - 86400  # Tiempo después de las 24 horas
                    expired_hours = int(total_expired_time // 3600)
                    expired_minutes = int((total_expired_time % 3600) // 60)
                    result["time_remaining"] = "EXPIRADO"
                    result["expired_since"] = f"{expired_hours}h {expired_minutes}m"
                    result["status_text"] = "EXPIRADO"
                    
            else:
                result["status"] = "no_data"
                result["time_remaining"] = "Sin registro"
                result["status_text"] = "SIN REGISTRO"
            
            return result

    async def get_all_bunkers_status(self, guild_id: str, server_name: str = "Default") -> List[Dict]:
        """Obtiene el estado de todos los bunkers de un servidor en un Discord guild específico"""
        bunkers = []
        for sector in ["D1", "C4", "A1", "A3"]:
            status = await self.get_bunker_status(sector, guild_id, server_name)
            if status:
                bunkers.append(status)
        return bunkers

    async def _schedule_notifications(self, sector: str, expiry_time: datetime, server_name: str = "Default", guild_id: str = ""):
        """Programa notificaciones para un bunker en un Discord guild específico"""
        async with aiosqlite.connect(self.db_path) as db:
            # Limpiar notificaciones anteriores
            await db.execute("""
                DELETE FROM notifications 
                WHERE bunker_sector = ? AND server_name = ? AND discord_guild_id = ?
            """, (sector, server_name, guild_id))
            
            # Programar nuevas notificaciones
            notifications = [
                (expiry_time - timedelta(hours=2), "2_hours_before"),
                (expiry_time - timedelta(minutes=30), "30_minutes_before"),
                (expiry_time, "bunker_opens"),
                (expiry_time + timedelta(hours=24), "bunker_closes")
            ]
            
            for notification_time, notification_type in notifications:
                if notification_time > datetime.now():
                    await db.execute("""
                        INSERT INTO notifications (bunker_sector, server_name, discord_guild_id, notification_time, notification_type)
                        VALUES (?, ?, ?, ?, ?)
                    """, (sector, server_name, guild_id, notification_time, notification_type))
            
            await db.commit()

    async def create_notification(self, sector: str, server_name: str, guild_id: str, notification_time: datetime, notification_type: str, registered_by_id: str = None):
        """Crea una notificación específica"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO notifications (bunker_sector, server_name, discord_guild_id, notification_time, notification_type, sent, registered_by_id)
                VALUES (?, ?, ?, ?, ?, FALSE, ?)
            """, (sector, server_name, guild_id, notification_time, notification_type, registered_by_id))
            await db.commit()

    async def get_pending_notifications(self, guild_id: str = None) -> List[Dict]:
        """Obtiene las notificaciones pendientes, opcionalmente filtradas por guild"""
        async with aiosqlite.connect(self.db_path) as db:
            if guild_id:
                cursor = await db.execute("""
                    SELECT n.id, n.bunker_sector, n.server_name, n.discord_guild_id, n.notification_time, n.notification_type, b.name, n.registered_by_id
                    FROM notifications n
                    JOIN bunkers b ON n.bunker_sector = b.sector AND n.server_name = b.server_name AND n.discord_guild_id = b.discord_guild_id
                    WHERE n.sent = FALSE AND n.notification_time <= ? AND n.discord_guild_id = ?
                """, (datetime.now(), guild_id))
            else:
                cursor = await db.execute("""
                    SELECT n.id, n.bunker_sector, n.server_name, n.discord_guild_id, n.notification_time, n.notification_type, b.name, n.registered_by_id
                    FROM notifications n
                    JOIN bunkers b ON n.bunker_sector = b.sector AND n.server_name = b.server_name AND n.discord_guild_id = b.discord_guild_id
                    WHERE n.sent = FALSE AND n.notification_time <= ?
                """, (datetime.now(),))
            
            notifications = []
            async for row in cursor:
                notifications.append({
                    "id": row[0],
                    "sector": row[1],
                    "server_name": row[2],
                    "discord_guild_id": row[3],
                    "time": row[4],
                    "type": row[5],
                    "name": row[6],
                    "registered_by_id": row[7]
                })
            
            return notifications

    async def mark_notification_sent(self, notification_id: int):
        """Marca una notificación como enviada"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE notifications SET sent = TRUE WHERE id = ?
            """, (notification_id,))
            await db.commit()

    async def get_unique_servers(self, guild_id: str):
        """Obtiene la lista de servidores únicos para un guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT DISTINCT server_name FROM bunkers 
                WHERE discord_guild_id = ? AND server_name IS NOT NULL
                ORDER BY server_name
            """, (guild_id,))
            
            servers = []
            async for row in cursor:
                servers.append(row[0])
            
            # Si no hay servidores, devolver "Default"
            if not servers:
                servers = ["Default"]
                
            return servers

    async def save_notification_config(self, guild_id: str, channel_id: str, server_name: str, 
                                     bunker_sector: str, notification_type: str, role_id: str = None, 
                                     enabled: bool = True, personal_dm: bool = False, created_by: str = None):
        """Guarda una configuración de notificación"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO notification_configs 
                (discord_guild_id, channel_id, server_name, bunker_sector, notification_type, role_id, enabled, personal_dm, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, channel_id, server_name, bunker_sector, notification_type, role_id, enabled, personal_dm, created_by))
            await db.commit()

    async def get_notification_configs(self, guild_id: str, server_name: str = None, bunker_sector: str = None):
        """Obtiene configuraciones de notificación que coincidan con los criterios"""
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT channel_id, role_id, notification_type, enabled, personal_dm, created_by 
                FROM notification_configs 
                WHERE discord_guild_id = ? AND enabled = TRUE
            """
            params = [guild_id]
            
            # Filtros opcionales
            if server_name:
                query += " AND (server_name = ? OR server_name = 'all_servers')"
                params.append(server_name)
            
            if bunker_sector:
                query += " AND (bunker_sector = ? OR bunker_sector = 'all_sectors')"
                params.append(bunker_sector)
            
            cursor = await db.execute(query, params)
            
            configs = []
            async for row in cursor:
                configs.append({
                    "channel_id": row[0],
                    "role_id": row[1],
                    "notification_type": row[2],
                    "enabled": row[3],
                    "personal_dm": row[4],
                    "created_by": row[5]
                })
            
            return configs

    async def check_daily_usage(self, guild_id: str, user_id: str) -> dict:
        """Verificar el uso del usuario (1 bunker cada 72 horas)"""
        from datetime import datetime, timedelta
        
        async with aiosqlite.connect(self.db_path) as db:
            # Asegurar que la columna existe
            try:
                await db.execute("ALTER TABLE daily_usage ADD COLUMN last_bunker_timestamp TIMESTAMP")
                await db.commit()
            except:
                pass  # Columna ya existe
            
            cursor = await db.execute("""
                SELECT last_bunker_timestamp, bunkers_registered
                FROM daily_usage 
                WHERE discord_guild_id = ? AND discord_user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (guild_id, user_id))
            
            row = await cursor.fetchone()
            
            if not row or not row[0]:
                # Usuario nunca ha registrado o no tiene timestamp
                return {
                    "bunkers_in_period": 0,
                    "last_registration": None,
                    "can_register": True,
                    "hours_remaining": 0,
                    "next_available": "Disponible ahora"
                }
            
            last_timestamp_str, bunkers_registered = row
            last_timestamp = datetime.fromisoformat(last_timestamp_str)
            now = datetime.now()
            
            # Calcular tiempo transcurrido desde último registro
            time_since_last = now - last_timestamp
            hours_since_last = time_since_last.total_seconds() / 3600
            
            # Verificar si han pasado 72 horas
            can_register = hours_since_last >= 72
            hours_remaining = max(0, 72 - hours_since_last)
            
            if hours_remaining > 0:
                next_available_time = last_timestamp + timedelta(hours=72)
                next_available = f"<t:{int(next_available_time.timestamp())}:R>"
            else:
                next_available = "Disponible ahora"
            
            return {
                "bunkers_in_period": 1 if hours_since_last < 72 else 0,
                "last_registration": last_timestamp.isoformat(),
                "can_register": can_register,
                "hours_remaining": round(hours_remaining, 1),
                "next_available": next_available
            }
    
    async def increment_daily_usage(self, guild_id: str, user_id: str):
        """Registrar nuevo uso del usuario (sistema 72 horas)"""
        from datetime import datetime, date
        now = datetime.now()
        today = date.today()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Asegurar que la columna existe
            try:
                await db.execute("ALTER TABLE daily_usage ADD COLUMN last_bunker_timestamp TIMESTAMP")
                await db.commit()
            except:
                pass  # Columna ya existe
            
            # Insertar nuevo registro con timestamp actual
            await db.execute("""
                INSERT OR REPLACE INTO daily_usage 
                (discord_guild_id, discord_user_id, usage_date, bunkers_registered, last_bunker_timestamp)
                VALUES (?, ?, ?, 1, ?)
            """, (guild_id, user_id, today, now.isoformat()))
            
            await db.commit()
    
    async def get_daily_usage_stats(self, guild_id: str, user_id: str, days: int = 7) -> list:
        """Obtener estadísticas de uso diario de los últimos N días"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT usage_date, bunkers_registered 
                FROM daily_usage 
                WHERE discord_guild_id = ? AND discord_user_id = ?
                ORDER BY usage_date DESC 
                LIMIT ?
            """, (guild_id, user_id, days))
            
            stats = []
            async for row in cursor:
                stats.append({
                    "date": row[0],
                    "bunkers_registered": row[1]
                })
            
            return stats
