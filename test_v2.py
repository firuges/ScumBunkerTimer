#!/usr/bin/env python3
"""
Script de prueba para la nueva funcionalidad V2 con soporte para servidores
"""

import asyncio
import logging
from database_v2 import BunkerDatabaseV2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_v2_functionality():
    """Probar toda la funcionalidad de la versión 2"""
    
    # Inicializar base de datos
    db = BunkerDatabaseV2("test_bunkers_v2.db")
    await db.initialize()
    
    logger.info("=== PRUEBAS BASE DE DATOS V2 ===")
    
    # 1. Probar gestión de servidores
    logger.info("1. Probando gestión de servidores...")
    
    # Agregar servidores de prueba
    await db.add_server("Servidor-EU", "Servidor Europeo", "TestUser")
    await db.add_server("Servidor-US", "Servidor Americano", "TestUser")
    await db.add_server("Test-PVP", "Servidor de pruebas PVP", "Admin")
    
    # Listar servidores
    servers = await db.get_servers()
    logger.info(f"Servidores creados: {len(servers)}")
    for server in servers:
        logger.info(f"  - {server['name']}: {server['description']}")
    
    # 2. Probar registro de bunkers en diferentes servidores
    logger.info("2. Probando registro de bunkers...")
    
    # Registrar bunkers en diferentes servidores
    await db.register_bunker_time("D1", 5, 30, "TestUser1", "123456", "Default")
    await db.register_bunker_time("C4", 2, 15, "TestUser2", "789012", "Servidor-EU")
    await db.register_bunker_time("A1", 1, 0, "TestUser3", "345678", "Servidor-US")
    await db.register_bunker_time("A3", 0, 45, "TestUser4", "901234", "Test-PVP")
    
    # 3. Probar consulta de estados
    logger.info("3. Probando consulta de estados...")
    
    servers_to_test = ["Default", "Servidor-EU", "Servidor-US", "Test-PVP"]
    
    for server_name in servers_to_test:
        logger.info(f"\n--- SERVIDOR: {server_name} ---")
        bunkers = await db.get_all_bunkers_status(server_name)
        
        for bunker in bunkers:
            status_info = f"{bunker['sector']}: {bunker['status_text']}"
            if bunker['status'] != 'no_data':
                status_info += f" - {bunker['time_remaining']}"
            logger.info(f"  {status_info}")
    
    # 4. Probar consulta individual
    logger.info("\n4. Probando consultas individuales...")
    
    test_cases = [
        ("D1", "Default"),
        ("C4", "Servidor-EU"),
        ("A1", "Servidor-US"),
        ("A3", "Test-PVP"),
        ("D1", "Servidor-NoExiste")  # Caso que no existe
    ]
    
    for sector, server in test_cases:
        status = await db.get_bunker_status(sector, server)
        if status:
            logger.info(f"  {server}/{sector}: {status['status_text']} - {status.get('time_remaining', 'N/A')}")
        else:
            logger.info(f"  {server}/{sector}: No encontrado")
    
    # 5. Probar eliminación de servidor
    logger.info("\n5. Probando eliminación de servidor...")
    
    # Intentar eliminar servidor Default (debería fallar)
    result = await db.remove_server("Default")
    logger.info(f"Eliminar Default: {result} (esperado: False)")
    
    # Eliminar servidor de prueba
    result = await db.remove_server("Test-PVP")
    logger.info(f"Eliminar Test-PVP: {result} (esperado: True)")
    
    # Verificar que se eliminó
    servers = await db.get_servers()
    logger.info(f"Servidores después de eliminación: {[s['name'] for s in servers]}")
    
    # 6. Probar notificaciones
    logger.info("\n6. Probando sistema de notificaciones...")
    
    notifications = await db.get_pending_notifications()
    logger.info(f"Notificaciones pendientes: {len(notifications)}")
    
    for notification in notifications[:3]:  # Mostrar solo las primeras 3
        logger.info(f"  {notification['server_name']}/{notification['sector']}: {notification['type']}")
    
    logger.info("\n=== PRUEBAS COMPLETADAS ===")

if __name__ == "__main__":
    asyncio.run(test_v2_functionality())
