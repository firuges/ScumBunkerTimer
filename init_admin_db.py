#!/usr/bin/env python3
"""
Script para inicializar las tablas del panel administrativo
"""

import sqlite3
import os
import sys

def init_admin_tables():
    """Initialize admin panel tables in the database"""
    
    # Path to database
    db_path = "scum_main.db"
    
    # Path to SQL file
    sql_file = "ADMIN_PANEL/create_admin_panel_tables.sql"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    try:
        # Read SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.executescript(sql_content)
        conn.commit()
        conn.close()
        
        print("✅ Admin panel tables initialized successfully!")
        print(f"✅ Database: {os.path.abspath(db_path)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing admin tables: {e}")
        return False

def verify_tables():
    """Verify that tables were created successfully"""
    
    db_path = "scum_main.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of admin tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'admin_%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        print(f"\n📊 Found {len(tables)} admin tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if we have expected tables
        expected_tables = [
            'admin_users', 'admin_sessions', 'admin_audit_logs', 
            'admin_settings', 'admin_backups', 'admin_templates',
            'admin_notifications', 'admin_analytics', 'admin_background_tasks',
            'admin_automation_rules', 'admin_webhooks'
        ]
        
        existing_table_names = [t[0] for t in tables]
        missing_tables = [t for t in expected_tables if t not in existing_table_names]
        
        if missing_tables:
            print(f"⚠️ Missing tables: {missing_tables}")
        else:
            print("✅ All expected admin tables found!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Initializing SCUM Bot Admin Panel Database...")
    print("=" * 50)
    
    if init_admin_tables():
        verify_tables()
        print("\n🎉 Admin panel database initialization complete!")
    else:
        print("\n❌ Admin panel database initialization failed!")
        sys.exit(1)