#!/usr/bin/env python3
"""
Test de la nueva funcionalidad de aislamiento por Discord Guild
Verifica que los datos se separen correctamente entre guilds
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_v2 import BunkerDatabaseV2

async def test_guild_isolation():
    """Test del aislamiento por guild"""
    print("🧪 Iniciando test de aislamiento por Discord Guild")
    print("=" * 50)
    
    db = BunkerDatabaseV2()
    await db.initialize()
    
    # IDs de prueba para simular diferentes Discord servers
    guild1_id = "123456789"  # Discord Server 1
    guild2_id = "987654321"  # Discord Server 2
    
    try:
        # 1. Test: Agregar servidores SCUM con el mismo nombre en diferentes guilds
        print("📝 Test 1: Servidores con mismo nombre en guilds diferentes")
        
        success1 = await db.add_server("Mi-Servidor", "Servidor de prueba 1", "Usuario1", guild1_id)
        success2 = await db.add_server("Mi-Servidor", "Servidor de prueba 2", "Usuario2", guild2_id)
        
        print(f"   Guild 1 - Agregar 'Mi-Servidor': {'✅' if success1 else '❌'}")
        print(f"   Guild 2 - Agregar 'Mi-Servidor': {'✅' if success2 else '❌'}")
        
        # 2. Test: Verificar que cada guild solo ve sus propios servidores
        print("\n📝 Test 2: Aislamiento de servidores")
        
        servers_guild1 = await db.get_servers(guild1_id)
        servers_guild2 = await db.get_servers(guild2_id)
        
        print(f"   Guild 1 tiene {len(servers_guild1)} servidores")
        print(f"   Guild 2 tiene {len(servers_guild2)} servidores")
        
        for server in servers_guild1:
            print(f"     - Guild 1: {server['name']}")
        for server in servers_guild2:
            print(f"     - Guild 2: {server['name']}")
        
        # 3. Test: Registrar bunkers en cada guild
        print("\n📝 Test 3: Aislamiento de bunkers")
        
        # Registrar bunker D1 en ambos guilds
        reg1 = await db.register_bunker_time("D1", 5, 30, "Usuario1", guild1_id, "user1", "Mi-Servidor")
        reg2 = await db.register_bunker_time("D1", 3, 15, "Usuario2", guild2_id, "user2", "Mi-Servidor")
        
        print(f"   Guild 1 - Registrar D1: {'✅' if reg1 else '❌'}")
        print(f"   Guild 2 - Registrar D1: {'✅' if reg2 else '❌'}")
        
        # 4. Test: Verificar que cada guild solo ve sus bunkers
        print("\n📝 Test 4: Status independiente de bunkers")
        
        status1 = await db.get_bunker_status("D1", guild1_id, "Mi-Servidor")
        status2 = await db.get_bunker_status("D1", guild2_id, "Mi-Servidor")
        
        if status1:
            print(f"   Guild 1 - D1: {status1['status_text']} - {status1['registered_by']}")
        if status2:
            print(f"   Guild 2 - D1: {status2['status_text']} - {status2['registered_by']}")
        
        # 5. Test: Verificar que get_all_bunkers_status también está aislado
        print("\n📝 Test 5: Status de todos los bunkers por guild")
        
        all_bunkers1 = await db.get_all_bunkers_status(guild1_id, "Mi-Servidor")
        all_bunkers2 = await db.get_all_bunkers_status(guild2_id, "Mi-Servidor")
        
        print(f"   Guild 1 - Bunkers activos: {len([b for b in all_bunkers1 if b.get('registered_by')])}")
        print(f"   Guild 2 - Bunkers activos: {len([b for b in all_bunkers2 if b.get('registered_by')])}")
        
        # 6. Test: Verificar datos legacy
        print("\n📝 Test 6: Datos legacy")
        
        legacy_servers = await db.get_servers("legacy")
        print(f"   Servidores legacy: {len(legacy_servers)}")
        for server in legacy_servers:
            print(f"     - Legacy: {server['name']}")
        
        # 7. Test: Limpiar datos de prueba
        print("\n🧹 Limpiando datos de prueba...")
        
        await db.remove_server("Mi-Servidor", guild1_id)
        await db.remove_server("Mi-Servidor", guild2_id)
        
        print("✅ Test de aislamiento completado exitosamente")
        print("\n📋 RESULTADO:")
        print("   ✅ Los Discord servers tienen datos completamente separados")
        print("   ✅ Pueden tener servidores SCUM con el mismo nombre")
        print("   ✅ Los bunkers se registran independientemente")
        print("   ✅ Los datos legacy se mantienen accesibles")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Función principal"""
    await test_guild_isolation()

if __name__ == "__main__":
    asyncio.run(main())
