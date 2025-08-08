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
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear tabla de bunkers (modificada para incluir servidor)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bunkers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sector TEXT NOT NULL,
                    name TEXT NOT NULL,
                    server_name TEXT DEFAULT 'Default',
                    registered_time TIMESTAMP,
                    expiry_time TIMESTAMP,
                    registered_by TEXT,
                    discord_user_id TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sector, server_name)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bunker_sector TEXT,
                    server_name TEXT DEFAULT 'Default',
                    notification_time TIMESTAMP,
                    notification_type TEXT,
                    sent BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Insertar servidor por defecto
            await db.execute("""
                INSERT OR IGNORE INTO servers (name, description, created_by) 
                VALUES ('Default', 'Servidor por defecto', 'System')
            """)
            
            # Insertar bunkers predeterminados para el servidor por defecto
            bunkers_data = [
                ("D1", "Bunker Abandonado D1"),
                ("C4", "Bunker Abandonado C4"),
                ("A1", "Bunker Abandonado A1"),
                ("A3", "Bunker Abandonado A3")
            ]
            
            for sector, name in bunkers_data:
                await db.execute("""
                    INSERT OR IGNORE INTO bunkers (sector, name, server_name) 
                    VALUES (?, ?, 'Default')
                """, (sector, name))
            
            await db.commit()
            logger.info("Base de datos V2 inicializada correctamente")

    # === GESTIÓN DE SERVIDORES ===
    
    async def add_server(self, name: str, description: str = "", created_by: str = "") -> bool:
        """Agregar un nuevo servidor"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO servers (name, description, created_by) 
                    VALUES (?, ?, ?)
                """, (name, description, created_by))
                
                # Crear bunkers para el nuevo servidor
                bunkers_data = [
                    ("D1", "Bunker Abandonado D1"),
                    ("C4", "Bunker Abandonado C4"),
                    ("A1", "Bunker Abandonado A1"),
                    ("A3", "Bunker Abandonado A3")
                ]
                
                for sector, bunker_name in bunkers_data:
                    await db.execute("""
                        INSERT INTO bunkers (sector, name, server_name) 
                        VALUES (?, ?, ?)
                    """, (sector, bunker_name, name))
                
                await db.commit()
                logger.info(f"Servidor '{name}' agregado correctamente")
                return True
                
        except Exception as e:
            logger.error(f"Error agregando servidor: {e}")
            return False

    async def remove_server(self, name: str) -> bool:
        """Eliminar un servidor y todos sus bunkers"""
        try:
            if name == 'Default':
                logger.warning("No se puede eliminar el servidor por defecto")
                return False
                
            async with aiosqlite.connect(self.db_path) as db:
                # Verificar si el servidor existe
                cursor = await db.execute("SELECT name FROM servers WHERE name = ?", (name,))
                if not await cursor.fetchone():
                    return False
                
                # Eliminar notificaciones del servidor
                await db.execute("DELETE FROM notifications WHERE server_name = ?", (name,))
                
                # Eliminar bunkers del servidor
                await db.execute("DELETE FROM bunkers WHERE server_name = ?", (name,))
                
                # Eliminar el servidor
                await db.execute("DELETE FROM servers WHERE name = ?", (name,))
                
                await db.commit()
                logger.info(f"Servidor '{name}' eliminado correctamente")
                return True
                
        except Exception as e:
            logger.error(f"Error eliminando servidor: {e}")
            return False

    async def get_servers(self) -> List[Dict]:
        """Obtener lista de servidores"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT name, description, created_by, created_at 
                FROM servers ORDER BY name
            """)
            
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
                                 registered_by: str, discord_user_id: str = None, 
                                 server_name: str = "Default") -> bool:
        """Registra el tiempo de un bunker en un servidor específico"""
        try:
            current_time = datetime.now()
            expiry_time = current_time + timedelta(hours=hours, minutes=minutes)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE bunkers 
                    SET registered_time = ?, expiry_time = ?, registered_by = ?, 
                        discord_user_id = ?, last_updated = ?
                    WHERE sector = ? AND server_name = ?
                """, (current_time, expiry_time, registered_by, discord_user_id, 
                      current_time, sector, server_name))
                
                await db.commit()
                
                # Programar notificaciones
                await self._schedule_notifications(sector, expiry_time, server_name)
                
                logger.info(f"Tiempo registrado para bunker {sector} en servidor {server_name}: {hours}h {minutes}m")
                return True
                
        except Exception as e:
            logger.error(f"Error registrando tiempo: {e}")
            return False

    async def get_bunker_status(self, sector: str, server_name: str = "Default") -> Optional[Dict]:
        """Obtiene el estado actual de un bunker en un servidor específico"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT sector, name, registered_time, expiry_time, registered_by, discord_user_id, server_name
                FROM bunkers WHERE sector = ? AND server_name = ?
            """, (sector, server_name))
            
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

    async def get_all_bunkers_status(self, server_name: str = "Default") -> List[Dict]:
        """Obtiene el estado de todos los bunkers de un servidor"""
        bunkers = []
        for sector in ["D1", "C4", "A1", "A3"]:
            status = await self.get_bunker_status(sector, server_name)
            if status:
                bunkers.append(status)
        return bunkers

    async def _schedule_notifications(self, sector: str, expiry_time: datetime, server_name: str = "Default"):
        """Programa notificaciones para un bunker"""
        async with aiosqlite.connect(self.db_path) as db:
            # Limpiar notificaciones anteriores
            await db.execute("""
                DELETE FROM notifications 
                WHERE bunker_sector = ? AND server_name = ?
            """, (sector, server_name))
            
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
                        INSERT INTO notifications (bunker_sector, server_name, notification_time, notification_type)
                        VALUES (?, ?, ?, ?)
                    """, (sector, server_name, notification_time, notification_type))
            
            await db.commit()

    async def get_pending_notifications(self) -> List[Dict]:
        """Obtiene las notificaciones pendientes"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT n.id, n.bunker_sector, n.server_name, n.notification_time, n.notification_type, b.name
                FROM notifications n
                JOIN bunkers b ON n.bunker_sector = b.sector AND n.server_name = b.server_name
                WHERE n.sent = FALSE AND n.notification_time <= ?
            """, (datetime.now(),))
            
            notifications = []
            async for row in cursor:
                notifications.append({
                    "id": row[0],
                    "sector": row[1],
                    "server_name": row[2],
                    "time": row[3],
                    "type": row[4],
                    "name": row[5]
                })
            
            return notifications

    async def mark_notification_sent(self, notification_id: int):
        """Marca una notificación como enviada"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE notifications SET sent = TRUE WHERE id = ?
            """, (notification_id,))
            await db.commit()
