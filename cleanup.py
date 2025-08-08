#!/usr/bin/env python3
"""
Script para limpiar archivos innecesarios y organizar el proyecto
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Limpiar y organizar archivos del proyecto"""
    
    # Archivos IMPORTANTES que se mantienen
    keep_files = {
        # Bot principal V2
        'BunkerAdvice_V2.py',
        'database_v2.py',
        
        # Configuración
        '.env',
        'requirements.txt',
        
        # Base de datos actual
        'bunkers_v2.db',
        
        # Documentación importante
        'README_V2.md',
        'COMANDOS_GUIA.md',
        'IMPLEMENTACION_COMPLETADA.md',
        
        # Scripts útiles
        'migrate_to_v2.py',
        'test_v2.py',
        'status_check.py',
        
        # Launcher
        'run_v2.bat',
        
        # Git
        '.git',
        '.gitignore'
    }
    
    # Archivos LEGACY que se mueven
    legacy_files = {
        # Bots antiguos
        'BunkerAdvice.py',
        'BunkerAdvice_Fixed.py', 
        'BunkerBot_SlashOnly.py',
        
        # Base de datos antigua
        'database.py',
        'bunkers.db',
        
        # Scripts de debug/test antiguos
        'debug_commands.py',
        'debug_registration.py',
        'debug_time.py',
        'test_bot.py',
        'test_commands.py',
        'test_simple.py',
        'test_states.py',
        'inspect_db.py',
        
        # Scripts de sync antiguos
        'fix_sync.py',
        'force_sync.py',
        'sync_commands.py',
        
        # Instaladores antiguos
        'install.bat',
        'run.bat',
        
        # Otros
        'README.md',
        'rcon_manager.py',
        '.env.example'
    }
    
    # Archivos TEMPORALES que se eliminan
    temp_files = {
        'bot.log',
        'test_bunkers_v2.db',
        '__pycache__'
    }
    
    # Crear carpeta legacy
    legacy_dir = Path('legacy')
    legacy_dir.mkdir(exist_ok=True)
    
    print("🧹 LIMPIANDO PROYECTO...")
    print("=" * 50)
    
    # Mover archivos legacy
    moved_count = 0
    for file in legacy_files:
        if os.path.exists(file):
            try:
                if os.path.isdir(file):
                    shutil.move(file, legacy_dir / file)
                else:
                    shutil.move(file, legacy_dir / file)
                print(f"📦 Movido a legacy: {file}")
                moved_count += 1
            except Exception as e:
                print(f"❌ Error moviendo {file}: {e}")
    
    # Eliminar archivos temporales
    deleted_count = 0
    for file in temp_files:
        if os.path.exists(file):
            try:
                if os.path.isdir(file):
                    shutil.rmtree(file)
                else:
                    os.remove(file)
                print(f"🗑️ Eliminado: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error eliminando {file}: {e}")
    
    # Mostrar archivos que se mantienen
    print(f"\n✅ ARCHIVOS PRINCIPALES MANTENIDOS:")
    for file in sorted(keep_files):
        if os.path.exists(file):
            print(f"   📄 {file}")
    
    # Archivos de backup
    backup_files = [f for f in os.listdir('.') if f.startswith('bunkers_backup_')]
    if backup_files:
        print(f"\n💾 BACKUPS MANTENIDOS:")
        for backup in backup_files:
            print(f"   💾 {backup}")
    
    print(f"\n📊 RESUMEN:")
    print(f"   📦 Archivos movidos a legacy: {moved_count}")
    print(f"   🗑️ Archivos eliminados: {deleted_count}")
    print(f"   ✅ Archivos principales: {len([f for f in keep_files if os.path.exists(f)])}")
    
    print(f"\n🎉 LIMPIEZA COMPLETADA!")
    print(f"💡 Para ejecutar el bot: python BunkerAdvice_V2.py")

if __name__ == "__main__":
    cleanup_project()
