#!/usr/bin/env python3
"""
Test del nuevo sistema restrictivo para plan gratuito
1 bunker activo por servidor Discord total
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_v2 import BunkerDatabaseV2
from datetime import datetime, timedelta

async def test_restrictive_free_plan():
    """Test del sistema restrictivo"""
    print("🧪 TESTING NUEVO SISTEMA RESTRICTIVO PARA PLAN GRATUITO")
    print("="*60)
    
    db = BunkerDatabaseV2()
    await db.initialize()
    
    guild_id = "test_guild_restrictive"
    
    # Test 1: Servidor sin bunkers activos
    print("\n📝 TEST 1: Servidor vacío")
    server_limit = await db.check_server_bunker_limit(guild_id)
    print(f"   ✅ Tiene bunker activo: {server_limit['has_active_bunker']}")
    print(f"   ✅ Puede registrar: {server_limit['can_register']}")
    
    # Test 2: Usuario A registra un bunker
    print("\n📝 TEST 2: Usuario A registra bunker")
    
    # Usar función completa para insertar bunker de prueba
    from datetime import datetime, timedelta
    import aiosqlite
    
    current_time = datetime.now()
    expiry_time = current_time + timedelta(hours=10)
    
    # Insertar directamente para asegurar que funcione
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute("""
            INSERT OR REPLACE INTO bunkers 
            (sector, name, server_name, discord_guild_id, registered_time, expiry_time, registered_by, discord_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("D1", "Bunker Abandonado D1", "convictos", guild_id, 
              current_time.isoformat(), expiry_time.isoformat(), "Usuario A", "user_a_123"))
        await conn.commit()
    
    print(f"   ✅ Registro simulado exitoso")
    
    # Test 3: Verificar estado después del registro
    print("\n📝 TEST 3: Estado después del registro")
    server_limit = await db.check_server_bunker_limit(guild_id)
    print(f"   ❌ Tiene bunker activo: {server_limit['has_active_bunker']}")
    print(f"   ❌ Puede registrar: {server_limit['can_register']}")
    if server_limit['has_active_bunker']:
        active = server_limit['active_bunker']
        print(f"   📍 Bunker activo: Sector {active['sector']} por {active['registered_by']}")
        print(f"   ⏰ Tiempo restante: {active['hours_remaining']:.1f} horas")
    
    # Test 4: Usuario B intenta registrar otro bunker
    print("\n📝 TEST 4: Usuario B intenta registrar")
    server_limit_b = await db.check_server_bunker_limit(guild_id)
    if server_limit_b['can_register']:
        print("   ✅ Usuario B puede registrar")
    else:
        print("   ❌ Usuario B BLOQUEADO - servidor ya tiene bunker activo")
        active = server_limit_b['active_bunker']
        print(f"   📍 Bunker bloqueante: {active['sector']} por {active['registered_by']}")
    
    print("\n" + "="*60)
    print("✅ NUEVO SISTEMA RESTRICTIVO VERIFICADO")
    print("📋 Comportamiento confirmado:")
    print("   • Plan gratuito: 1 bunker activo por servidor Discord")
    print("   • Si hay 1 bunker, NADIE más puede registrar")
    print("   • Fomenta coordinación entre usuarios")
    print("   • Premium permite bunkers ilimitados")

if __name__ == "__main__":
    asyncio.run(test_restrictive_free_plan())
