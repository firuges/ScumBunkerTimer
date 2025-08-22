#!/usr/bin/env python3
"""
Sistema de Base de Datos para Tickets
Maneja la tabla tickets en scum_main.db
"""

import aiosqlite
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class TicketDatabase:
    def __init__(self, db_path: str = "scum_main.db"):
        self.db_path = db_path

    async def initialize(self):
        """Inicializar tabla de tickets"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_number INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    discord_id TEXT NOT NULL,
                    discord_guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    subject TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP NULL,
                    closed_by TEXT NULL
                )
            """)
            
            # Índices para optimizar consultas
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickets_user_guild_status 
                ON tickets(user_id, discord_guild_id, status)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickets_guild_status 
                ON tickets(discord_guild_id, status)
            """)
            
            await db.commit()
            logger.info("✅ Tabla tickets inicializada correctamente")

    async def initialize_ticket_channels_table(self):
        """Inicializar tabla de canales de tickets activos"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ticket_channels (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    message_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
            logger.info("✅ Tabla ticket_channels inicializada correctamente")

    async def get_next_ticket_number(self, guild_id: str) -> int:
        """Obtener siguiente número de ticket para el servidor"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT MAX(ticket_number) FROM tickets 
                WHERE discord_guild_id = ?
            """, (guild_id,))
            
            result = await cursor.fetchone()
            max_number = result[0] if result[0] else 0
            return max_number + 1

    async def create_ticket(self, user_id: str, discord_id: str, guild_id: str, 
                          channel_id: str, ticket_number: int, subject: str = None) -> int:
        """Crear nuevo ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO tickets (ticket_number, user_id, discord_id, discord_guild_id, 
                                   channel_id, subject, status)
                VALUES (?, ?, ?, ?, ?, ?, 'open')
            """, (ticket_number, user_id, discord_id, guild_id, channel_id, subject))
            
            await db.commit()
            ticket_id = cursor.lastrowid
            
            logger.info(f"🎫 Ticket creado: ID={ticket_id}, Número={ticket_number}, Usuario={discord_id}")
            return ticket_id

    async def add_ticket_channel(self, channel_id: str, user_id: str, guild_id: str, message_id: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT INTO ticket_channels (channel_id, user_id, guild_id, message_id) VALUES (?, ?, ?, ?)',
                (channel_id, user_id, guild_id, message_id)
            )
            await db.commit()

    async def remove_ticket_channel(self, channel_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM ticket_channels WHERE channel_id = ?', (channel_id,))
            await db.commit()

    async def get_active_ticket_channels(self, guild_id: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            if guild_id:
                cursor = await db.execute('''
                    SELECT tc.* FROM ticket_channels tc
                    JOIN tickets t ON tc.channel_id = t.channel_id
                    WHERE tc.guild_id = ? AND t.status = 'open'
                ''', (guild_id,))
            else:
                cursor = await db.execute('''
                    SELECT tc.* FROM ticket_channels tc
                    JOIN tickets t ON tc.channel_id = t.channel_id
                    WHERE t.status = 'open'
                ''')
            return await cursor.fetchall()

    async def get_ticket_channel_by_user(self, user_id: str, guild_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM ticket_channels WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
            return await cursor.fetchone()

    async def has_active_ticket(self, user_id: str, guild_id: str) -> bool:
        """Verificar si usuario tiene ticket activo"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) FROM tickets 
                WHERE user_id = ? AND discord_guild_id = ? AND status = 'open'
            """, (user_id, guild_id))
            
            result = await cursor.fetchone()
            return result[0] > 0

    async def get_active_ticket(self, user_id: str, guild_id: str) -> Optional[Dict]:
        """Obtener ticket activo del usuario"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT ticket_id, ticket_number, channel_id, subject, created_at
                FROM tickets 
                WHERE user_id = ? AND discord_guild_id = ? AND status = 'open'
                LIMIT 1
            """, (user_id, guild_id))
            
            result = await cursor.fetchone()
            if result:
                return {
                    'ticket_id': result[0],
                    'ticket_number': result[1],
                    'channel_id': result[2],
                    'subject': result[3],
                    'created_at': result[4]
                }
            return None

    async def get_ticket_by_number(self, ticket_number: int, guild_id: str) -> Optional[Dict]:
        """Obtener ticket por número"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT ticket_id, user_id, discord_id, channel_id, status, subject, created_at
                FROM tickets 
                WHERE ticket_number = ? AND discord_guild_id = ?
            """, (ticket_number, guild_id))
            
            result = await cursor.fetchone()
            if result:
                return {
                    'ticket_id': result[0],
                    'user_id': result[1],
                    'discord_id': result[2],
                    'channel_id': result[3],
                    'status': result[4],
                    'subject': result[5],
                    'created_at': result[6]
                }
            return None

    async def get_ticket_by_channel(self, channel_id: str) -> Optional[Dict]:
        """Obtener ticket por canal (solo tickets abiertos)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT ticket_id, ticket_number, user_id, discord_id, discord_guild_id, 
                       status, subject, created_at
                FROM tickets 
                WHERE channel_id = ? AND status = 'open'
            """, (channel_id,))
            
            result = await cursor.fetchone()
            logger.info(f"Obteniendo ticket por canal {channel_id}: {result}")
            if result:
                return {
                    'ticket_id': result[0],
                    'ticket_number': result[1],
                    'user_id': result[2],
                    'discord_id': result[3],
                    'guild_id': result[4],
                    'status': result[5],
                    'subject': result[6],
                    'created_at': result[7]
                }
            return None

    async def close_ticket(self, ticket_id: int, closed_by: str) -> bool:
        """Cerrar ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE tickets 
                SET status = 'closed', closed_at = CURRENT_TIMESTAMP, closed_by = ?
                WHERE ticket_id = ? AND status = 'open'
            """, (closed_by, ticket_id))
            
            await db.commit()
            updated = cursor.rowcount > 0
            
            if updated:
                logger.info(f"🔒 Ticket {ticket_id} cerrado por {closed_by}")
            
            return updated

    async def get_active_tickets(self, guild_id: str) -> List[Dict]:
        """Obtener todos los tickets activos del servidor"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT t.ticket_id, t.ticket_number, t.discord_id, u.username,
                       t.channel_id, t.subject, t.created_at
                FROM tickets t
                LEFT JOIN users u ON t.user_id = u.user_id
                WHERE t.discord_guild_id = ? AND t.status = 'open'
                ORDER BY t.ticket_number ASC
            """, (guild_id,))
            
            results = await cursor.fetchall()
            tickets = []
            
            for result in results:
                tickets.append({
                    'ticket_id': result[0],
                    'ticket_number': result[1],
                    'discord_id': result[2],
                    'username': result[3],
                    'channel_id': result[4],
                    'subject': result[5],
                    'created_at': result[6]
                })
            
            return tickets

    async def get_ticket_stats(self, guild_id: str) -> Dict:
        """Obtener estadísticas de tickets del servidor"""
        async with aiosqlite.connect(self.db_path) as db:
            # Tickets totales
            cursor = await db.execute("""
                SELECT COUNT(*) FROM tickets WHERE discord_guild_id = ?
            """, (guild_id,))
            total = (await cursor.fetchone())[0]
            
            # Tickets activos
            cursor = await db.execute("""
                SELECT COUNT(*) FROM tickets 
                WHERE discord_guild_id = ? AND status = 'open'
            """, (guild_id,))
            active = (await cursor.fetchone())[0]
            
            # Tickets cerrados
            cursor = await db.execute("""
                SELECT COUNT(*) FROM tickets 
                WHERE discord_guild_id = ? AND status = 'closed'
            """, (guild_id,))
            closed = (await cursor.fetchone())[0]
            
            return {
                'total': total,
                'active': active,
                'closed': closed
            }

    async def set_ticket_panel_message_id(self, guild_id: str, channel_id: str, message_id: str):
        """Guardar el message_id del panel principal de tickets para restaurar la vista"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ticket_panel (
                    guild_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    message_id TEXT NOT NULL
                )
            """)
            await db.execute(
                'INSERT OR REPLACE INTO ticket_panel (guild_id, channel_id, message_id) VALUES (?, ?, ?)',
                (guild_id, channel_id, message_id)
            )
            await db.commit()

    async def get_ticket_panel_message_id(self, guild_id: str):
        """Obtener el message_id del panel principal de tickets para restaurar la vista"""
        async with aiosqlite.connect(self.db_path) as db:
            # Asegurar que la tabla existe
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ticket_panel (
                    guild_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    message_id TEXT NOT NULL
                )
            """)
            
            cursor = await db.execute('SELECT channel_id, message_id FROM ticket_panel WHERE guild_id = ?', (guild_id,))
            result = await cursor.fetchone()
            if result:
                return {'channel_id': result[0], 'message_id': result[1]}
            return None