#!/usr/bin/env python3
"""
Script para migrar la base de datos y agregar soporte para DM personal
"""
import aiosqlite
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_database():
    """Migrar base de datos para agregar columnas de DM personal"""
    db_path = "bunkers_v2.db"
    
    try:
        async with aiosqlite.connect(db_path) as db:
            # Agregar columna registered_by_id a notifications si no existe
            try:
                await db.execute("ALTER TABLE notifications ADD COLUMN registered_by_id TEXT")
                logger.info("✅ Columna registered_by_id agregada a notifications")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("ℹ️ Columna registered_by_id ya existe en notifications")
                else:
                    logger.error(f"Error agregando registered_by_id: {e}")
            
            # Agregar columna personal_dm a notification_configs si no existe
            try:
                await db.execute("ALTER TABLE notification_configs ADD COLUMN personal_dm BOOLEAN DEFAULT FALSE")
                logger.info("✅ Columna personal_dm agregada a notification_configs")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("ℹ️ Columna personal_dm ya existe en notification_configs")
                else:
                    logger.error(f"Error agregando personal_dm: {e}")
            
            await db.commit()
            logger.info("🎉 Migración completada exitosamente")
            
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")

if __name__ == "__main__":
    asyncio.run(migrate_database())
