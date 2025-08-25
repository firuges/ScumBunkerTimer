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
    sql_file = "create_fame_tables.sql"
    
    if not os.path.exists(db_path):
        print("Database file not found: " + db_path)
        return False
    
    if not os.path.exists(sql_file):
        print("SQL file not found: " + sql_file)
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
        
        print("SUCCESS: Admin panel tables initialized!")
        print("Database: " + os.path.abspath(db_path))
        
        return True
        
    except Exception as e:
        print("ERROR initializing admin tables: " + str(e))
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
        
        print("Found " + str(len(tables)) + " admin tables:")
        for table in tables:
            print("  - " + table[0])
        
        # Check if we have expected tables
        expected_tables = ['admin_fame_rewards']
        
        existing_table_names = [t[0] for t in tables]
        missing_tables = [t for t in expected_tables if t not in existing_table_names]
        
        if missing_tables:
            print("Missing tables: " + str(missing_tables))
        else:
            print("All expected admin tables found!")
        
        conn.close()
        return True
        
    except Exception as e:
        print("ERROR verifying tables: " + str(e))
        return False

if __name__ == "__main__":
    print("Initializing SCUM Bot Admin Panel Database...")
    print("=" * 50)
    
    if init_admin_tables():
        verify_tables()
        print("Admin panel database initialization complete!")
    else:
        print("Admin panel database initialization failed!")
        sys.exit(1)