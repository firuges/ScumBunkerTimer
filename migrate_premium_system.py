#!/usr/bin/env python3
"""
Script de migración para inicializar el sistema de suscripciones
Crea las tablas necesarias y configuración inicial
"""

import asyncio
import logging
from subscription_manager import SubscriptionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_subscription_system():
    """Migrar e inicializar sistema de suscripciones"""
    print("🚀 Inicializando Sistema de Suscripciones Premium")
    print("=" * 60)
    
    try:
        # Inicializar sistema de suscripciones
        sub_manager = SubscriptionManager()
        await sub_manager.initialize()
        
        print("✅ Base de datos de suscripciones creada")
        print("✅ Planes configurados:")
        print("   🆓 Free: 2 bunkers, 1 servidor, $0/mes")
        print("   💎 Premium: Ilimitado, $5.99/mes")  
        print("   🏢 Enterprise: Ilimitado + extras, $15.99/mes")
        
        # Verificar que todo funciona
        test_guild = "test_guild_123"
        subscription = await sub_manager.get_subscription(test_guild)
        print(f"✅ Test de suscripción: {subscription['plan_type']}")
        
        # Limpiar test
        await sub_manager.cancel_subscription(test_guild)
        
        print("\n🎉 SISTEMA DE SUSCRIPCIONES LISTO")
        print("📋 PRÓXIMOS PASOS:")
        print("1. Deploy del bot actualizado")
        print("2. Configurar Stripe (opcional)")
        print("3. Promocionar en comunidades SCUM")
        print("4. Gestionar suscripciones con /ba_admin_premium")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        return False

async def main():
    """Función principal"""
    success = await migrate_subscription_system()
    if success:
        print("\n✅ Migración completada exitosamente")
    else:
        print("\n❌ Migración falló")

if __name__ == "__main__":
    asyncio.run(main())
