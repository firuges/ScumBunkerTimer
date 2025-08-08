#!/usr/bin/env python3
"""
Script de migración para agregar aislamiento por Discord Guild
Convierte la base de datos existente para separar datos por servidor de Discord
"""

import asyncio
import aiosqlite
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_PATH = "bunkers_v2.db"
BACKUP_PATH = f"bunkers_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

async def backup_database():
    """Crear copia de respaldo de la base de datos"""
    try:
        # Leer la base original
        async with aiosqlite.connect(DATABASE_PATH) as source:
            # Crear respaldo
            async with aiosqlite.connect(BACKUP_PATH) as backup:
                await source.backup(backup)
        
        print(f"✅ Respaldo creado: {BACKUP_PATH}")
        return True
    except Exception as e:
        print(f"❌ Error creando respaldo: {e}")
        return False

async def migrate_database():
    """Migrar base de datos para incluir guild_id"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            # 1. Verificar si ya tiene las columnas guild_id
            cursor = await db.execute("PRAGMA table_info(servers)")
            columns = await cursor.fetchall()
            has_guild_id = any(col[1] == 'discord_guild_id' for col in columns)
            
            if has_guild_id:
                print("⚠️ La base de datos ya tiene la migración aplicada")
                return True
            
            print("🔄 Iniciando migración...")
            
            # 2. Agregar columna guild_id a servers (con valor por defecto)
            await db.execute("ALTER TABLE servers ADD COLUMN discord_guild_id TEXT DEFAULT 'legacy'")
            print("✅ Columna discord_guild_id agregada a servers")
            
            # 3. Agregar columna guild_id a bunkers
            await db.execute("ALTER TABLE bunkers ADD COLUMN discord_guild_id TEXT DEFAULT 'legacy'")
            print("✅ Columna discord_guild_id agregada a bunkers")
            
            # 4. Agregar columna guild_id a notifications
            await db.execute("ALTER TABLE notifications ADD COLUMN discord_guild_id TEXT DEFAULT 'legacy'")
            print("✅ Columna discord_guild_id agregada a notifications")
            
            # 5. Actualizar constraints (recrear tablas con nuevos UNIQUE)
            print("🔄 Actualizando constraints...")
            
            # Crear nueva tabla servers con constraint correcto
            await db.execute("""
                CREATE TABLE servers_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_by TEXT,
                    discord_guild_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, discord_guild_id)
                )
            """)
            
            # Copiar datos
            await db.execute("""
                INSERT INTO servers_new (id, name, description, created_by, discord_guild_id, created_at)
                SELECT id, name, description, created_by, 
                       COALESCE(discord_guild_id, 'legacy'), created_at 
                FROM servers
            """)
            
            # Intercambiar tablas
            await db.execute("DROP TABLE servers")
            await db.execute("ALTER TABLE servers_new RENAME TO servers")
            print("✅ Tabla servers actualizada")
            
            # Crear nueva tabla bunkers con constraint correcto
            await db.execute("""
                CREATE TABLE bunkers_new (
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
            
            # Copiar datos
            await db.execute("""
                INSERT INTO bunkers_new (id, sector, name, server_name, discord_guild_id, 
                                       registered_time, expiry_time, registered_by, 
                                       discord_user_id, last_updated)
                SELECT id, sector, name, server_name, 
                       COALESCE(discord_guild_id, 'legacy'),
                       registered_time, expiry_time, registered_by, 
                       discord_user_id, last_updated 
                FROM bunkers
            """)
            
            # Intercambiar tablas
            await db.execute("DROP TABLE bunkers")
            await db.execute("ALTER TABLE bunkers_new RENAME TO bunkers")
            print("✅ Tabla bunkers actualizada")
            
            await db.commit()
            print("✅ Migración completada exitosamente")
            
            # 6. Mostrar estadísticas
            cursor = await db.execute("SELECT COUNT(*) FROM servers")
            servers_count = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM bunkers")
            bunkers_count = (await cursor.fetchone())[0]
            
            print(f"📊 Datos migrados:")
            print(f"   - {servers_count} servidores")
            print(f"   - {bunkers_count} bunkers")
            print(f"   - Todos marcados con guild_id 'legacy'")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en migración: {e}")
            await db.rollback()
            return False

async def main():
    """Función principal"""
    print("🚀 Iniciando migración de base de datos para aislamiento por Discord Guild")
    print("=" * 70)
    
    # 1. Crear respaldo
    if not await backup_database():
        print("❌ No se pudo crear respaldo. Abortando migración.")
        return
    
    # 2. Realizar migración
    if await migrate_database():
        print("\n✅ MIGRACIÓN COMPLETADA")
        print("🔄 Reinicia el bot para que use la nueva estructura")
        print(f"💾 Respaldo guardado en: {BACKUP_PATH}")
        print("\n📝 NOTAS IMPORTANTES:")
        print("- Los datos existentes están marcados como 'legacy'")
        print("- Cada Discord server tendrá sus propios datos a partir de ahora")
        print("- Los servidores SCUM pueden tener el mismo nombre en diferentes Discord servers")
    else:
        print("\n❌ MIGRACIÓN FALLÓ")
        print("🔄 Restaura el respaldo si es necesario")

if __name__ == "__main__":
    asyncio.run(main())
