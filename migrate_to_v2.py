#!/usr/bin/env python3
"""
Script de migración para transferir datos de la base de datos antigua a la nueva versión
con soporte para múltiples servidores
"""

import asyncio
import aiosqlite
import logging
from datetime import datetime
from database_v2 import BunkerDatabaseV2
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_data():
    """Migrar datos de la base de datos antigua a la nueva"""
    old_db_path = "bunkers.db"
    new_db_path = "bunkers_v2.db"
    
    # Verificar si existe la base de datos antigua
    if not os.path.exists(old_db_path):
        logger.info("No se encontró base de datos antigua. Iniciando con base de datos nueva.")
        # Crear nueva base de datos
        new_db = BunkerDatabaseV2(new_db_path)
        await new_db.initialize()
        logger.info("Nueva base de datos V2 inicializada correctamente.")
        return
    
    logger.info("Iniciando migración de datos...")
    
    # Crear nueva base de datos
    new_db = BunkerDatabaseV2(new_db_path)
    await new_db.initialize()
    
    # Conectar a la base de datos antigua
    async with aiosqlite.connect(old_db_path) as old_conn:
        # Migrar bunkers
        cursor = await old_conn.execute("""
            SELECT sector, name, registered_time, expiry_time, registered_by, discord_user_id
            FROM bunkers
        """)
        
        bunkers_migrated = 0
        async for row in cursor:
            sector, name, registered_time, expiry_time, registered_by, discord_user_id = row
            
            # Insertar en la nueva base de datos con servidor "Default"
            async with aiosqlite.connect(new_db_path) as new_conn:
                await new_conn.execute("""
                    UPDATE bunkers 
                    SET registered_time = ?, expiry_time = ?, registered_by = ?, discord_user_id = ?
                    WHERE sector = ? AND server_name = 'Default'
                """, (registered_time, expiry_time, registered_by, discord_user_id, sector))
                await new_conn.commit()
            
            bunkers_migrated += 1
            logger.info(f"Migrado bunker {sector}")
        
        # Migrar notificaciones
        try:
            cursor = await old_conn.execute("""
                SELECT bunker_sector, notification_time, notification_type, sent
                FROM notifications
            """)
            
            notifications_migrated = 0
            async for row in cursor:
                bunker_sector, notification_time, notification_type, sent = row
                
                # Insertar en la nueva base de datos con servidor "Default"
                async with aiosqlite.connect(new_db_path) as new_conn:
                    await new_conn.execute("""
                        INSERT INTO notifications (bunker_sector, server_name, notification_time, notification_type, sent)
                        VALUES (?, 'Default', ?, ?, ?)
                    """, (bunker_sector, notification_time, notification_type, sent))
                    await new_conn.commit()
                
                notifications_migrated += 1
                logger.info(f"Migrada notificación para {bunker_sector}")
            
        except Exception as e:
            logger.warning(f"Error migrando notificaciones (puede que no existan): {e}")
            notifications_migrated = 0
    
    logger.info(f"Migración completada:")
    logger.info(f"  - Bunkers migrados: {bunkers_migrated}")
    logger.info(f"  - Notificaciones migradas: {notifications_migrated}")
    
    # Crear backup de la base de datos antigua
    backup_name = f"bunkers_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        import shutil
        shutil.copy2(old_db_path, backup_name)
        logger.info(f"Backup creado: {backup_name}")
    except Exception as e:
        logger.error(f"Error creando backup: {e}")

async def verify_migration():
    """Verificar que la migración fue exitosa"""
    logger.info("Verificando migración...")
    
    db = BunkerDatabaseV2("bunkers_v2.db")
    await db.initialize()
    
    # Verificar servidores
    servers = await db.get_servers()
    logger.info(f"Servidores en nueva DB: {len(servers)}")
    
    # Verificar bunkers del servidor Default
    bunkers = await db.get_all_bunkers_status("Default")
    logger.info(f"Bunkers en servidor Default: {len(bunkers)}")
    
    for bunker in bunkers:
        logger.info(f"  - {bunker['sector']}: {bunker['status_text']}")

if __name__ == "__main__":
    async def main():
        await migrate_data()
        await verify_migration()
    
    asyncio.run(main())
