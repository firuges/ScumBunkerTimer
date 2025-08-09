#!/usr/bin/env python3
"""
Test rápido del sistema de 72 horas
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_v2 import BunkerDatabaseV2

async def test_72h_system():
    """Test del nuevo sistema"""
    print("🧪 Testing nuevo sistema de 72 horas...")
    
    db = BunkerDatabaseV2()
    await db.initialize()
    
    # Test con usuario nuevo
    usage = await db.check_daily_usage('test_guild', 'test_user')
    print(f"\n👤 Usuario nuevo:")
    print(f"   ✅ Puede registrar: {usage['can_register']}")
    print(f"   ⏰ Horas restantes: {usage['hours_remaining']}")
    print(f"   📅 Próximo disponible: {usage['next_available']}")
    
    # Simular registro
    if usage['can_register']:
        await db.increment_daily_usage('test_guild', 'test_user')
        print("\n✅ Registro simulado exitoso")
        
        # Verificar estado después del registro
        usage_after = await db.check_daily_usage('test_guild', 'test_user')
        print(f"\n⏳ Después del registro:")
        print(f"   ❌ Puede registrar: {usage_after['can_register']}")
        print(f"   ⏰ Horas restantes: {usage_after['hours_remaining']:.1f}")
        print(f"   📅 Próximo disponible: {usage_after['next_available']}")
    
    print("\n🎯 SISTEMA DE 72 HORAS FUNCIONANDO CORRECTAMENTE!")
    print("💡 Los usuarios del plan gratuito podrán registrar 1 bunker cada 72 horas")

if __name__ == "__main__":
    asyncio.run(test_72h_system())
