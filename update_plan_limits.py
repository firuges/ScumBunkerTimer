#!/usr/bin/env python3
"""
Script para actualizar los límites del plan gratuito a 1 bunker por día
"""

import asyncio
import aiosqlite

async def update_plan_limits():
    """Actualizar los límites del plan gratuito"""
    db_path = "subscriptions.db"
    
    try:
        async with aiosqlite.connect(db_path) as db:
            # Actualizar límites del plan gratuito
            await db.execute("""
                UPDATE plan_limits 
                SET max_bunkers = 1
                WHERE plan_type = 'free'
            """)
            
            await db.commit()
            print("✅ Límites del plan gratuito actualizados a 1 bunker por día")
            
            # Verificar cambios
            cursor = await db.execute("""
                SELECT plan_type, max_bunkers, max_servers 
                FROM plan_limits 
                ORDER BY plan_type
            """)
            
            rows = await cursor.fetchall()
            print("\n📊 Límites actuales:")
            for row in rows:
                plan_type, max_bunkers, max_servers = row
                bunkers_text = "ilimitados" if max_bunkers == -1 else f"{max_bunkers} por día"
                servers_text = "ilimitados" if max_servers == -1 else f"{max_servers}"
                print(f"• {plan_type.capitalize()}: {bunkers_text}, {servers_text} servidor(es)")
            
    except Exception as e:
        print(f"❌ Error actualizando límites: {e}")

if __name__ == "__main__":
    asyncio.run(update_plan_limits())
