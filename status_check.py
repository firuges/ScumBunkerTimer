#!/usr/bin/env python3
"""
Script de verificación rápida del estado del bot V2
"""

import asyncio
import os
from database_v2 import BunkerDatabaseV2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def quick_status():
    """Mostrar estado rápido del sistema"""
    print("=" * 50)
    print("    SCUM BUNKER BOT V2 - ESTADO DEL SISTEMA")
    print("=" * 50)
    
    # Verificar archivos
    print("\n📁 ARCHIVOS:")
    files_to_check = [
        ("bunkers.db", "Base de datos V1 (Original)"),
        ("bunkers_v2.db", "Base de datos V2 (Multi-servidor)"),
        ("BunkerAdvice_Fixed.py", "Bot V1 (Legacy)"),
        ("BunkerAdvice_V2.py", "Bot V2 (Multi-servidor)"),
        ("database.py", "Módulo DB V1"),
        ("database_v2.py", "Módulo DB V2"),
    ]
    
    for filename, description in files_to_check:
        status = "✅" if os.path.exists(filename) else "❌"
        print(f"  {status} {filename} - {description}")
    
    # Verificar backups
    backup_files = [f for f in os.listdir('.') if f.startswith('bunkers_backup_')]
    if backup_files:
        print(f"\n💾 BACKUPS ENCONTRADOS: {len(backup_files)}")
        for backup in sorted(backup_files):
            print(f"  📄 {backup}")
    else:
        print("\n💾 BACKUPS: Ninguno encontrado")
    
    # Verificar base de datos V2
    if os.path.exists("bunkers_v2.db"):
        print("\n🗃️ BASE DE DATOS V2:")
        try:
            db = BunkerDatabaseV2("bunkers_v2.db")
            await db.initialize()
            
            # Servidores
            servers = await db.get_servers()
            print(f"  📡 Servidores registrados: {len(servers)}")
            for server in servers:
                print(f"    - {server['name']}: {server['description']}")
            
            # Estado de bunkers por servidor
            print(f"\n🏗️ ESTADO DE BUNKERS:")
            for server in servers:
                print(f"\n  📡 {server['name']}:")
                bunkers = await db.get_all_bunkers_status(server['name'])
                for bunker in bunkers:
                    status_icon = {"closed": "🔒", "active": "🟢", "expired": "🔴", "no_data": "❓"}
                    icon = status_icon.get(bunker['status'], "❓")
                    time_info = bunker.get('time_remaining', 'N/A')
                    print(f"    {icon} {bunker['sector']}: {bunker['status_text']} - {time_info}")
            
        except Exception as e:
            print(f"  ❌ Error accediendo a la base de datos: {e}")
    else:
        print("\n🗃️ BASE DE DATOS V2: No encontrada")
    
    # Variables de entorno
    print("\n🔧 CONFIGURACIÓN:")
    discord_token = os.getenv('DISCORD_TOKEN')
    if discord_token:
        print(f"  ✅ DISCORD_TOKEN: Configurado ({discord_token[:10]}...)")
    else:
        print("  ❌ DISCORD_TOKEN: No configurado")
    
    print("\n" + "=" * 50)
    print("✅ Verificación completada")
    print("💡 Para ejecutar el bot V2: python BunkerAdvice_V2.py")
    print("💡 Para migrar desde V1: python migrate_to_v2.py")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(quick_status())
