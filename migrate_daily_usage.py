#!/usr/bin/env python3
"""
Script para agregar el sistema de uso diario (1 bunker por día para plan gratuito)
"""

import asyncio
import aiosqlite
from datetime import date

async def migrate_daily_usage_system():
    """Agregar tabla de uso diario"""
    db_path = "bunkers_v2.db"
    
    try:
        async with aiosqlite.connect(db_path) as db:
            # Crear tabla de uso diario
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
            
            await db.commit()
            print("✅ Tabla daily_usage creada correctamente")
            
            # Verificar que la tabla se creó
            cursor = await db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='daily_usage'
            """)
            
            table_exists = await cursor.fetchone()
            if table_exists:
                print("✅ Tabla daily_usage verificada en la base de datos")
                
                # Mostrar estructura de la tabla
                cursor = await db.execute("PRAGMA table_info(daily_usage)")
                columns = await cursor.fetchall()
                print("\n📋 Estructura de la tabla daily_usage:")
                for col in columns:
                    print(f"• {col[1]} ({col[2]})")
            else:
                print("❌ Error: Tabla daily_usage no encontrada")
            
            print(f"\n💡 Sistema de uso diario implementado:")
            print(f"• Plan Gratuito: 1 bunker por día")
            print(f"• Plan Premium: Bunkers ilimitados")
            print(f"• Tracking por usuario y fecha")
            
    except Exception as e:
        print(f"❌ Error en migración: {e}")

if __name__ == "__main__":
    asyncio.run(migrate_daily_usage_system())
