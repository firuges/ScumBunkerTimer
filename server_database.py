#!/usr/bin/env python3
"""
Base de datos para sistema de monitoreo de servidores SCUM
"""

import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ServerDatabase:
    def __init__(self, db_path: str = "bunkers_v2.db"):
        self.db_path = db_path
    
    async def initialize_server_tables(self):
        """Inicializar tablas para monitoreo de servidores"""
        async with aiosqlite.connect(self.db_path) as db:
            # Tabla de servidores monitoreados
            await db.execute('''
                CREATE TABLE IF NOT EXISTS monitored_servers (
                    server_id TEXT PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    server_name TEXT NOT NULL,
                    server_ip TEXT NOT NULL,
                    server_port INTEGER DEFAULT 7777,
                    battlemetrics_id TEXT,
                    added_by TEXT NOT NULL,
                    added_at REAL NOT NULL,
                    alerts_enabled BOOLEAN DEFAULT 1,
                    last_status TEXT,
                    last_players INTEGER DEFAULT 0,
                    last_check REAL,
                    UNIQUE(guild_id, server_name)
                )
            ''')
            
            # Tabla de historial de estado
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    players_online INTEGER,
                    max_players INTEGER,
                    checked_at REAL NOT NULL,
                    FOREIGN KEY (server_id) REFERENCES monitored_servers (server_id)
                )
            ''')
            
            # Tabla de límites por guild
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_monitor_limits (
                    guild_id TEXT PRIMARY KEY,
                    max_servers INTEGER DEFAULT 5,
                    updated_by TEXT,
                    updated_at REAL
                )
            ''')
            
            await db.commit()
            logger.info("Tablas de monitoreo de servidores inicializadas")
    
    async def add_monitored_server(self, guild_id: str, server_name: str, server_ip: str, 
                                 server_port: int, battlemetrics_id: str, added_by: str) -> bool:
        """Agregar servidor para monitorear"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                server_id = f"{guild_id}_{server_name.lower().replace(' ', '_')}"
                current_time = datetime.now().timestamp()
                
                await db.execute('''
                    INSERT INTO monitored_servers 
                    (server_id, guild_id, server_name, server_ip, server_port, 
                     battlemetrics_id, added_by, added_at, alerts_enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (server_id, guild_id, server_name, server_ip, server_port, 
                      battlemetrics_id, added_by, current_time))
                
                await db.commit()
                logger.info(f"Servidor {server_name} agregado para guild {guild_id}")
                return True
                
        except aiosqlite.IntegrityError:
            logger.warning(f"Servidor {server_name} ya existe para guild {guild_id}")
            return False
        except Exception as e:
            logger.error(f"Error agregando servidor {server_name}: {e}")
            return False
    
    async def remove_monitored_server(self, guild_id: str, server_name: str) -> bool:
        """Remover servidor del monitoreo y limpiar todas las suscripciones relacionadas"""
        try:
            server_id = f"{guild_id}_{server_name.lower().replace(' ', '_')}"
            
            # === LIMPIEZA COMPLETA DE DATOS RELACIONADOS ===
            
            # Limpiar datos del sistema de monitoreo (server_database)
            async with aiosqlite.connect(self.db_path) as db:
                # 1. Eliminar historial de estado del servidor
                await db.execute(
                    'DELETE FROM server_status_history WHERE server_id = ?',
                    (server_id,)
                )
                logger.info(f"Eliminado historial de estado para servidor '{server_name}' en guild {guild_id}")
                
                # 2. Eliminar servidor de la tabla principal
                cursor = await db.execute(
                    'DELETE FROM monitored_servers WHERE server_id = ?',
                    (server_id,)
                )
                
                await db.commit()
                server_deleted = cursor.rowcount > 0
            
            # Limpiar datos del sistema de alertas de reinicio (taxi_database)
            try:
                from taxi_database import taxi_db
                
                # 3. Eliminar suscripciones de alertas de reinicio de usuarios
                async with aiosqlite.connect(taxi_db.db_path) as taxi_conn:
                    await taxi_conn.execute(
                        'DELETE FROM user_reset_alerts WHERE server_name = ? AND guild_id = ?',
                        (server_name, guild_id)
                    )
                    logger.info(f"Eliminadas suscripciones de alertas de reinicio para servidor '{server_name}' en guild {guild_id}")
                    
                    # 4. Eliminar historial de alertas enviadas (tabla correcta: reset_alert_cache)
                    await taxi_conn.execute(
                        'DELETE FROM reset_alert_cache WHERE server_name = ? AND guild_id = ?',
                        (server_name, guild_id)
                    )
                    logger.info(f"Eliminado caché de alertas enviadas para servidor '{server_name}' en guild {guild_id}")
                    
                    # 5. Eliminar horarios de reinicio programados
                    await taxi_conn.execute(
                        'DELETE FROM reset_schedules WHERE server_name = ?',
                        (server_name,)
                    )
                    logger.info(f"Eliminados horarios de reinicio para servidor '{server_name}'")
                    
                    await taxi_conn.commit()
                    
            except ImportError:
                logger.warning("taxi_database no disponible para limpieza de alertas de reinicio")
            except Exception as taxi_error:
                logger.error(f"Error limpiando datos de alertas de reinicio: {taxi_error}")
                
            if server_deleted:
                logger.info(f"Servidor '{server_name}' eliminado completamente del guild {guild_id} con limpieza de suscripciones")
                return True
            else:
                logger.warning(f"Servidor {server_name} no encontrado en guild {guild_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error eliminando servidor {server_name}: {e}")
            return False
    
    async def get_monitored_servers(self, guild_id: str) -> List[Dict]:
        """Obtener servidores monitoreados de un guild"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT server_id, server_name, server_ip, server_port, 
                           battlemetrics_id, added_by, added_at, alerts_enabled,
                           last_status, last_players, last_check
                    FROM monitored_servers 
                    WHERE guild_id = ?
                    ORDER BY added_at ASC
                ''', (guild_id,))
                
                servers = []
                async for row in cursor:
                    servers.append({
                        'server_id': row[0],
                        'server_name': row[1],
                        'server_ip': row[2],
                        'server_port': row[3],
                        'battlemetrics_id': row[4],
                        'added_by': row[5],
                        'added_at': row[6],
                        'alerts_enabled': bool(row[7]),
                        'last_status': row[8],
                        'last_players': row[9],
                        'last_check': row[10]
                    })
                
                return servers
                
        except Exception as e:
            logger.error(f"Error obteniendo servidores monitoreados: {e}")
            return []
    
    async def get_server_by_name(self, guild_id: str, server_name: str) -> Optional[Dict]:
        """Obtener servidor específico por nombre"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT server_id, server_name, server_ip, server_port, 
                           battlemetrics_id, alerts_enabled, last_status, last_players
                    FROM monitored_servers 
                    WHERE guild_id = ? AND server_name = ?
                ''', (guild_id, server_name))
                
                row = await cursor.fetchone()
                if row:
                    return {
                        'server_id': row[0],
                        'server_name': row[1],
                        'server_ip': row[2],
                        'server_port': row[3],
                        'battlemetrics_id': row[4],
                        'alerts_enabled': bool(row[5]),
                        'last_status': row[6],
                        'last_players': row[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo servidor {server_name}: {e}")
            return None
    
    async def update_server_status(self, server_id: str, status_data: Dict):
        """Actualizar estado del servidor"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().timestamp()
                
                # Actualizar último estado
                await db.execute('''
                    UPDATE monitored_servers 
                    SET last_status = ?, last_players = ?, last_check = ?
                    WHERE server_id = ?
                ''', (
                    'online' if status_data.get('online') else 'offline',
                    status_data.get('players', 0),
                    current_time,
                    server_id
                ))
                
                # Agregar al historial
                await db.execute('''
                    INSERT INTO server_status_history 
                    (server_id, status, players_online, max_players, checked_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    server_id,
                    'online' if status_data.get('online') else 'offline',
                    status_data.get('players', 0),
                    status_data.get('max_players', 0),
                    current_time
                ))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error actualizando estado del servidor {server_id}: {e}")
    
    async def toggle_server_alerts(self, guild_id: str, server_name: str, enabled: bool) -> bool:
        """Activar/desactivar alertas para un servidor"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    UPDATE monitored_servers 
                    SET alerts_enabled = ?
                    WHERE guild_id = ? AND server_name = ?
                ''', (enabled, guild_id, server_name))
                
                await db.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Alertas {'habilitadas' if enabled else 'deshabilitadas'} para {server_name}")
                    return True
                else:
                    return False
                
        except Exception as e:
            logger.error(f"Error cambiando alertas para {server_name}: {e}")
            return False
    
    async def check_server_limit(self, guild_id: str) -> Dict:
        """Verificar límite de servidores para un guild"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Obtener límite configurado
                cursor = await db.execute(
                    'SELECT max_servers FROM server_monitor_limits WHERE guild_id = ?',
                    (guild_id,)
                )
                row = await cursor.fetchone()
                max_servers = row[0] if row else 5  # Default: 5 servidores
                
                # Contar servidores actuales
                cursor = await db.execute(
                    'SELECT COUNT(*) FROM monitored_servers WHERE guild_id = ?',
                    (guild_id,)
                )
                current_count = (await cursor.fetchone())[0]
                
                return {
                    'current_count': current_count,
                    'max_servers': max_servers,
                    'can_add': current_count < max_servers,
                    'remaining': max_servers - current_count
                }
                
        except Exception as e:
            logger.error(f"Error verificando límites para guild {guild_id}: {e}")
            return {'current_count': 0, 'max_servers': 5, 'can_add': True, 'remaining': 5}
    
    async def set_server_limit(self, guild_id: str, max_servers: int, updated_by: str) -> bool:
        """Configurar límite de servidores para un guild (comando admin)"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now().timestamp()
                
                await db.execute('''
                    INSERT OR REPLACE INTO server_monitor_limits 
                    (guild_id, max_servers, updated_by, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (guild_id, max_servers, updated_by, current_time))
                
                await db.commit()
                logger.info(f"Límite de servidores configurado a {max_servers} para guild {guild_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error configurando límite para guild {guild_id}: {e}")
            return False

# Instancia global
server_db = ServerDatabase()
