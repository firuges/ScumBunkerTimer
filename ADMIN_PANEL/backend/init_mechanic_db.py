#!/usr/bin/env python3
"""
Script para inicializar las tablas del Sistema Mecánico en la base de datos SCUM Bot
"""

import sqlite3
import os
import sys

def init_mechanic_database():
    """Inicializar tablas del sistema mecánico en la base de datos"""
    
    # Ruta a la base de datos principal
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'scum_main.db')
    db_path = os.path.abspath(db_path)
    
    print(f"Inicializando Sistema Mecanico en: {db_path}")
    
    # Verificar que la base de datos existe
    if not os.path.exists(db_path):
        print(f"❌ Error: Base de datos no encontrada en {db_path}")
        return False
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Leer el archivo SQL
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_mechanic_tables.sql')
        
        if not os.path.exists(sql_file_path):
            print(f"❌ Error: Archivo SQL no encontrado en {sql_file_path}")
            return False
        
        print("📄 Leyendo archivo SQL...")
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        print("🏗️ Ejecutando creación de tablas...")
        
        # Ejecutar el script SQL completo
        cursor.executescript(sql_script)
        
        # Confirmar cambios
        conn.commit()
        
        # Verificar que las tablas se crearon correctamente
        print("✅ Verificando tablas creadas...")
        
        expected_tables = [
            'mechanic_services',
            'registered_mechanics', 
            'mechanic_preferences',
            'insurance_history',
            'vehicle_prices',
            'admin_mechanic_config'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%mechanic%' OR name LIKE '%insurance%' OR name LIKE '%vehicle_prices%'")
        created_tables = [row[0] for row in cursor.fetchall()]
        
        print("📊 Tablas encontradas:")
        for table in created_tables:
            print(f"  ✅ {table}")
        
        # Verificar datos de ejemplo
        print("\n📈 Verificando datos de ejemplo...")
        
        # Verificar configuración
        cursor.execute("SELECT COUNT(*) FROM admin_mechanic_config WHERE guild_id = '123456789'")
        config_count = cursor.fetchone()[0]
        print(f"  📋 Configuraciones: {config_count}")
        
        # Verificar mecánicos
        cursor.execute("SELECT COUNT(*) FROM registered_mechanics WHERE discord_guild_id = '123456789'")
        mechanics_count = cursor.fetchone()[0]
        print(f"  🔧 Mecánicos registrados: {mechanics_count}")
        
        # Verificar precios de vehículos
        cursor.execute("SELECT COUNT(*) FROM vehicle_prices WHERE guild_id = '123456789'")
        prices_count = cursor.fetchone()[0]
        print(f"  🚗 Precios de vehículos: {prices_count}")
        
        # Verificar servicios de ejemplo
        cursor.execute("SELECT COUNT(*) FROM mechanic_services WHERE guild_id = '123456789'")
        services_count = cursor.fetchone()[0]
        print(f"  🛠️ Servicios de ejemplo: {services_count}")
        
        conn.close()
        
        print(f"\n🎉 ¡Sistema Mecánico inicializado exitosamente!")
        print(f"📊 Resumen:")
        print(f"  • {len(created_tables)} tablas creadas")
        print(f"  • {config_count} configuración base")
        print(f"  • {mechanics_count} mecánicos de ejemplo")
        print(f"  • {prices_count} precios configurados")
        print(f"  • {services_count} servicios históricos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SCUM Bot - Inicialización Sistema Mecánico")
    print("=" * 50)
    
    success = init_mechanic_database()
    
    if success:
        print("\n✅ Inicialización completada exitosamente")
        print("🔗 Listo para integrar con Admin Panel")
        sys.exit(0)
    else:
        print("\n❌ Error en la inicialización")
        sys.exit(1)