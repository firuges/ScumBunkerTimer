#!/usr/bin/env python3
"""
Script para inicializar las tablas del sistema bancario
"""

import sqlite3
import os
import sys

def init_banking_tables():
    """Initialize banking system tables in the database"""
    
    # Path to database
    db_path = "scum_main.db"
    
    # Path to SQL file
    sql_file = "create_banking_tables.sql"
    
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
        
        print("SUCCESS: Banking system tables initialized!")
        print("Database: " + os.path.abspath(db_path))
        
        return True
        
    except Exception as e:
        print("ERROR initializing banking tables: " + str(e))
        return False

def verify_banking_tables():
    """Verify that banking tables were created successfully"""
    
    db_path = "scum_main.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of banking tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'admin_banking_%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        print("Found " + str(len(tables)) + " banking tables:")
        for table in tables:
            print("  - " + table[0])
        
        # Check specific table and count records
        cursor.execute("SELECT COUNT(*) FROM admin_banking_config")
        config_count = cursor.fetchone()[0]
        print("Banking configs: " + str(config_count))
        
        cursor.execute("SELECT COUNT(*) FROM admin_banking_account_types")
        account_types_count = cursor.fetchone()[0]
        print("Account types: " + str(account_types_count))
        
        cursor.execute("SELECT COUNT(*) FROM admin_banking_fees")
        fees_count = cursor.fetchone()[0]
        print("Banking fees: " + str(fees_count))
        
        conn.close()
        return True
        
    except Exception as e:
        print("ERROR verifying banking tables: " + str(e))
        return False

if __name__ == "__main__":
    print("Initializing SCUM Bot Banking System Database...")
    print("=" * 50)
    
    if init_banking_tables():
        verify_banking_tables()
        print("Banking system database initialization complete!")
    else:
        print("Banking system database initialization failed!")
        sys.exit(1)