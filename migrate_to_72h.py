#!/usr/bin/env python3
"""
Script para migrar el sistema de uso diario a sistema de 72 horas
Cambia de "1 bunker por día" a "1 bunker cada 72 horas"
"""

import asyncio
import aiosqlite
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_to_72h_system():
    """Migrar de sistema diario a sistema de 72 horas"""
    db_path = "bunkers_v2.db"
    
    try:
        async with aiosqlite.connect(db_path) as db:
            logger.info("🔄 Iniciando migración a sistema de 72 horas...")
            
            # 1. Agregar nueva columna para último registro
            try:
                await db.execute("ALTER TABLE daily_usage ADD COLUMN last_bunker_timestamp TIMESTAMP")
                logger.info("✅ Columna last_bunker_timestamp agregada")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("ℹ️ Columna last_bunker_timestamp ya existe")
                else:
                    logger.error(f"Error agregando columna: {e}")
            
            # 2. Migrar datos existentes
            # Para usuarios que ya registraron hoy, establecer timestamp como hace 71 horas
            # Así pueden registrar en 1 hora más
            cursor = await db.execute("""
                SELECT discord_guild_id, discord_user_id, usage_date, bunkers_registered
                FROM daily_usage 
                WHERE bunkers_registered > 0 AND last_bunker_timestamp IS NULL
            """)
            
            rows = await cursor.fetchall()
            migrated_users = 0
            
            for row in rows:
                guild_id, user_id, usage_date, bunkers_registered = row
                
                # Calcular timestamp: 71 horas atrás desde ahora
                # Esto da 1 hora de gracia para el primer uso del nuevo sistema
                last_timestamp = datetime.now() - timedelta(hours=71)
                
                await db.execute("""
                    UPDATE daily_usage 
                    SET last_bunker_timestamp = ?
                    WHERE discord_guild_id = ? AND discord_user_id = ? AND usage_date = ?
                """, (last_timestamp, guild_id, user_id, usage_date))
                
                migrated_users += 1
                logger.info(f"Migrado usuario {user_id} en guild {guild_id}")
            
            await db.commit()
            
            logger.info(f"✅ Migración completada:")
            logger.info(f"   📊 {migrated_users} usuarios migrados")
            logger.info(f"   ⏰ Sistema cambiado a: 1 bunker cada 72 horas")
            logger.info(f"   🎁 Usuarios existentes pueden registrar en ~1 hora")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error en migración: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(migrate_to_72h_system())
