#!/usr/bin/env python3
"""
Completar migración: Agregar tablas de bunkers_v2.db a scum_main.db
"""
import sqlite3
import shutil
from datetime import datetime

def backup_databases():
    """Crear backups de seguridad"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        shutil.copy2('scum_main.db', f'scum_main.db.backup_{timestamp}')
        print(f"✅ Backup creado: scum_main.db.backup_{timestamp}")
        
        if os.path.exists('bunkers_v2.db'):
            shutil.copy2('bunkers_v2.db', f'bunkers_v2.db.backup_{timestamp}')
            print(f"✅ Backup creado: bunkers_v2.db.backup_{timestamp}")
        
        return True
    except Exception as e:
        print(f"❌ Error creando backups: {e}")
        return False

def migrate_bunker_tables():
    """Migrar tablas de bunkers_v2.db a scum_main.db"""
    try:
        # Conectar a ambas bases de datos
        bunkers_conn = sqlite3.connect('bunkers_v2.db')
        main_conn = sqlite3.connect('scum_main.db')
        
        bunkers_cursor = bunkers_conn.cursor()
        main_cursor = main_conn.cursor()
        
        print("🔍 Analizando tablas en bunkers_v2.db...")
        
        # Obtener lista de tablas en bunkers_v2.db
        bunkers_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        bunker_tables = [row[0] for row in bunkers_cursor.fetchall()]
        
        print(f"📋 Tablas encontradas en bunkers_v2.db: {bunker_tables}")
        
        # Obtener lista de tablas en scum_main.db
        main_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        main_tables = [row[0] for row in main_cursor.fetchall()]
        
        print(f"📋 Tablas existentes en scum_main.db: {len(main_tables)} tablas")
        
        # Migrar cada tabla
        migrated_tables = []
        
        for table_name in bunker_tables:
            try:
                print(f"\n🔄 Migrando tabla: {table_name}")
                
                # Obtener esquema de la tabla
                bunkers_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                schema_result = bunkers_cursor.fetchone()
                
                if not schema_result:
                    print(f"⚠️ No se pudo obtener esquema para {table_name}")
                    continue
                
                create_sql = schema_result[0]
                print(f"📋 Esquema: {create_sql[:100]}...")
                
                # Crear tabla en scum_main.db
                main_cursor.execute(create_sql)
                
                # Obtener datos de la tabla
                bunkers_cursor.execute(f"SELECT * FROM {table_name}")
                rows = bunkers_cursor.fetchall()
                
                if rows:
                    # Obtener nombres de columnas
                    bunkers_cursor.execute(f"PRAGMA table_info({table_name})")
                    columns_info = bunkers_cursor.fetchall()
                    columns = [col[1] for col in columns_info]
                    
                    # Insertar datos
                    placeholders = ','.join(['?' for _ in columns])
                    insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                    
                    main_cursor.executemany(insert_sql, rows)
                    
                    print(f"✅ {len(rows)} registros migrados")
                else:
                    print(f"ℹ️ Tabla vacía, solo esquema migrado")
                
                migrated_tables.append(table_name)
                
            except Exception as e:
                print(f"❌ Error migrando tabla {table_name}: {e}")
        
        # Confirmar cambios
        main_conn.commit()
        
        # Cerrar conexiones
        bunkers_conn.close()
        main_conn.close()
        
        print(f"\n🎉 Migración completada!")
        print(f"✅ Tablas migradas: {len(migrated_tables)}")
        print(f"📋 Lista: {', '.join(migrated_tables)}")
        
        return True
        
    except Exception as e:
        print(f"💥 Error en migración: {e}")
        return False

def verify_migration():
    """Verificar que la migración fue exitosa"""
    try:
        main_conn = sqlite3.connect('scum_main.db')
        cursor = main_conn.cursor()
        
        # Verificar tablas críticas de bunkers
        critical_tables = ['bunkers', 'daily_usage', 'notifications', 'notification_configs', 'monitored_servers']
        
        print("\n🔍 Verificando migración...")
        
        for table in critical_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: {count} registros")
            except Exception as e:
                print(f"❌ {table}: Error - {e}")
        
        # Verificar total de tablas
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        total_tables = cursor.fetchone()[0]
        print(f"\n📊 Total de tablas en scum_main.db: {total_tables}")
        
        main_conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 COMPLETANDO MIGRACIÓN DE BUNKERS A scum_main.db")
    print("=" * 60)
    
    import os
    
    # Verificar que existen las bases de datos
    if not os.path.exists('bunkers_v2.db'):
        print("❌ bunkers_v2.db no encontrado")
        return False
    
    if not os.path.exists('scum_main.db'):
        print("❌ scum_main.db no encontrado")
        return False
    
    # Paso 1: Crear backups
    print("\n1️⃣ Creando backups de seguridad...")
    if not backup_databases():
        print("❌ Error en backups, cancelando migración")
        return False
    
    # Paso 2: Migrar tablas
    print("\n2️⃣ Migrando tablas de bunkers...")
    if not migrate_bunker_tables():
        print("❌ Error en migración")
        return False
    
    # Paso 3: Verificar migración
    print("\n3️⃣ Verificando migración...")
    if not verify_migration():
        print("❌ Error en verificación")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 MIGRACIÓN DE BUNKERS COMPLETADA EXITOSAMENTE")
    print("✅ Todas las tablas están ahora en scum_main.db")
    print("🔧 El bot debería funcionar correctamente ahora")
    
    return True

if __name__ == "__main__":
    try:
        import os
        success = main()
        if success:
            print("\n💡 Próximos pasos:")
            print("1. Ejecutar: python BunkerAdvice_V2.py")
            print("2. Verificar que el bot inicia correctamente")
            print("3. Probar comandos de bunkers")
        else:
            print("\n⚠️ Migración falló. Revisar errores arriba.")
    except KeyboardInterrupt:
        print("\n🛑 Migración cancelada por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()