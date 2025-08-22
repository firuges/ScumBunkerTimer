#!/usr/bin/env python3
"""
Base de Datos para Fame Point Rewards
Maneja reclamaciones de puntos de fama y configuraciones
"""

import aiosqlite
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class FameRewardsDatabase:
    def __init__(self, db_path: str = "scum_main.db"):
        self.db_path = db_path

    async def initialize(self):
        """Inicializar tablas de fame rewards"""
        async with aiosqlite.connect(self.db_path) as db:
            # Tabla de reclamaciones de puntos de fama
            await db.execute("""
                CREATE TABLE IF NOT EXISTS fame_point_claims (
                    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    discord_id TEXT NOT NULL,
                    discord_guild_id TEXT NOT NULL,
                    fame_amount INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP NULL,
                    confirmed_by TEXT NULL,
                    notification_message_id TEXT NULL
                )
            """)
            
            # Tabla de configuración de valores de fama disponibles por guild
            await db.execute("""
                CREATE TABLE IF NOT EXISTS fame_point_config (
                    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    fame_values TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id)
                )
            """)
            
            # Índices para optimizar consultas
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_fame_claims_user_guild_status 
                ON fame_point_claims(user_id, discord_guild_id, status)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_fame_claims_guild_status_fame 
                ON fame_point_claims(discord_guild_id, status, fame_amount, claimed_at)
            """)
            
            await db.commit()
            logger.info("✅ Tablas de Fame Point Rewards inicializadas correctamente")

    async def get_fame_config(self, guild_id: str) -> List[int]:
        """Obtener valores de fama configurados para el guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT fame_values FROM fame_point_config 
                WHERE guild_id = ?
            """, (guild_id,))
            
            result = await cursor.fetchone()
            if result:
                # Los valores se guardan como string separado por comas
                return [int(x) for x in result[0].split(",")]
            else:
                # Valores por defecto
                return [100, 500, 1000, 2000, 5000, 10000, 15000]

    async def set_fame_config(self, guild_id: str, fame_values: List[int]):
        """Establecer valores de fama configurables para el guild"""
        async with aiosqlite.connect(self.db_path) as db:
            fame_values_str = ",".join(map(str, fame_values))
            
            await db.execute("""
                INSERT OR REPLACE INTO fame_point_config (guild_id, fame_values, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (guild_id, fame_values_str))
            
            await db.commit()
            logger.info(f"✅ Configuración de fama actualizada para guild {guild_id}: {fame_values}")

    async def create_fame_claim(self, user_id: str, discord_id: str, guild_id: str, 
                               fame_amount: int, notification_message_id: str = None) -> int:
        """Crear nueva reclamación de puntos de fama"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO fame_point_claims (user_id, discord_id, discord_guild_id, 
                                             fame_amount, notification_message_id, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (user_id, discord_id, guild_id, fame_amount, notification_message_id))
            
            await db.commit()
            claim_id = cursor.lastrowid
            
            logger.info(f"🏆 Reclamación de fama creada: ID={claim_id}, Usuario={discord_id}, Fama={fame_amount}")
            return claim_id

    async def confirm_fame_claim(self, claim_id: int, confirmed_by: str) -> bool:
        """Confirmar reclamación de puntos de fama"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE fame_point_claims 
                SET status = 'confirmed', confirmed_at = CURRENT_TIMESTAMP, confirmed_by = ?
                WHERE claim_id = ? AND status = 'pending'
            """, (confirmed_by, claim_id))
            
            await db.commit()
            updated = cursor.rowcount > 0
            
            if updated:
                logger.info(f"✅ Reclamación de fama {claim_id} confirmada por {confirmed_by}")
            
            return updated

    async def reject_fame_claim(self, claim_id: int, rejected_by: str) -> bool:
        """Rechazar reclamación de puntos de fama"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE fame_point_claims 
                SET status = 'rejected', confirmed_at = CURRENT_TIMESTAMP, confirmed_by = ?
                WHERE claim_id = ? AND status = 'pending'
            """, (rejected_by, claim_id))
            
            await db.commit()
            updated = cursor.rowcount > 0
            
            if updated:
                logger.info(f"❌ Reclamación de fama {claim_id} rechazada por {rejected_by}")
            
            return updated

    async def get_claim_by_id(self, claim_id: int) -> Optional[Dict]:
        """Obtener reclamación por ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT claim_id, user_id, discord_id, discord_guild_id, fame_amount, 
                       status, claimed_at, confirmed_at, confirmed_by, notification_message_id
                FROM fame_point_claims 
                WHERE claim_id = ?
            """, (claim_id,))
            
            result = await cursor.fetchone()
            if result:
                return {
                    'claim_id': result[0],
                    'user_id': result[1],
                    'discord_id': result[2],
                    'guild_id': result[3],
                    'fame_amount': result[4],
                    'status': result[5],
                    'claimed_at': result[6],
                    'confirmed_at': result[7],
                    'confirmed_by': result[8],
                    'notification_message_id': result[9]
                }
            return None

    async def get_top_fame_claims(self, guild_id: str, limit: int = 10) -> List[Dict]:
        """Obtener top de reclamaciones confirmadas por fama y tiempo"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT fc.claim_id, fc.discord_id, u.ingame_name, fc.fame_amount, fc.claimed_at
                FROM fame_point_claims fc
                LEFT JOIN users u ON fc.user_id = u.user_id
                WHERE fc.discord_guild_id = ? AND fc.status = 'confirmed'
                ORDER BY fc.fame_amount DESC, fc.claimed_at ASC
                LIMIT ?
            """, (guild_id, limit))
            
            results = await cursor.fetchall()
            top_claims = []
            
            for result in results:
                top_claims.append({
                    'claim_id': result[0],
                    'discord_id': result[1],
                    'ingame_name': result[2],
                    'fame_amount': result[3],
                    'claimed_at': result[4]
                })
            
            return top_claims

    async def get_user_claims(self, user_id: str, guild_id: str) -> List[Dict]:
        """Obtener reclamaciones de un usuario específico"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT claim_id, fame_amount, status, claimed_at, confirmed_at
                FROM fame_point_claims 
                WHERE user_id = ? AND discord_guild_id = ?
                ORDER BY claimed_at DESC
            """, (user_id, guild_id))
            
            results = await cursor.fetchall()
            claims = []
            
            for result in results:
                claims.append({
                    'claim_id': result[0],
                    'fame_amount': result[1],
                    'status': result[2],
                    'claimed_at': result[3],
                    'confirmed_at': result[4]
                })
            
            return claims

    async def get_fame_stats(self, guild_id: str) -> Dict:
        """Obtener estadísticas de reclamaciones de fama del servidor"""
        async with aiosqlite.connect(self.db_path) as db:
            # Total de reclamaciones
            cursor = await db.execute("""
                SELECT COUNT(*) FROM fame_point_claims WHERE discord_guild_id = ?
            """, (guild_id,))
            total = (await cursor.fetchone())[0]
            
            # Reclamaciones pendientes
            cursor = await db.execute("""
                SELECT COUNT(*) FROM fame_point_claims 
                WHERE discord_guild_id = ? AND status = 'pending'
            """, (guild_id,))
            pending = (await cursor.fetchone())[0]
            
            # Reclamaciones confirmadas
            cursor = await db.execute("""
                SELECT COUNT(*) FROM fame_point_claims 
                WHERE discord_guild_id = ? AND status = 'confirmed'
            """, (guild_id,))
            confirmed = (await cursor.fetchone())[0]
            
            # Reclamaciones rechazadas
            cursor = await db.execute("""
                SELECT COUNT(*) FROM fame_point_claims 
                WHERE discord_guild_id = ? AND status = 'rejected'
            """, (guild_id,))
            rejected = (await cursor.fetchone())[0]
            
            return {
                'total': total,
                'pending': pending,
                'confirmed': confirmed,
                'rejected': rejected
            }

    async def has_pending_claim(self, user_id: str, guild_id: str) -> bool:
        """Verificar si el usuario tiene alguna reclamación pendiente"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) FROM fame_point_claims 
                WHERE user_id = ? AND discord_guild_id = ? AND status = 'pending'
            """, (user_id, guild_id))
            
            result = await cursor.fetchone()
            return result[0] > 0

    async def has_claimed_fame_amount(self, user_id: str, guild_id: str, fame_amount: int) -> bool:
        """Verificar si el usuario ya reclamó confirmadamente esta cantidad específica de fama"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) FROM fame_point_claims 
                WHERE user_id = ? AND discord_guild_id = ? AND fame_amount = ? AND status = 'confirmed'
            """, (user_id, guild_id, fame_amount))
            
            result = await cursor.fetchone()
            return result[0] > 0

    async def get_pending_claims(self, guild_id: str) -> List[Dict]:
        """Obtener todas las reclamaciones pendientes del servidor"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT fc.claim_id, fc.discord_id, u.ingame_name, fc.fame_amount, fc.claimed_at, fc.notification_message_id
                FROM fame_point_claims fc
                LEFT JOIN users u ON fc.user_id = u.user_id
                WHERE fc.discord_guild_id = ? AND fc.status = 'pending'
                ORDER BY fc.claimed_at ASC
            """, (guild_id,))
            
            results = await cursor.fetchall()
            pending_claims = []
            
            for result in results:
                pending_claims.append({
                    'claim_id': result[0],
                    'discord_id': result[1],
                    'ingame_name': result[2],
                    'fame_amount': result[3],
                    'claimed_at': result[4],
                    'notification_message_id': result[5]
                })
            
            return pending_claims