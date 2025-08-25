#!/usr/bin/env python3
"""
Script para inicializar las tablas del sistema de taxis
"""

import sqlite3
import os
import sys

def init_taxi_tables():
    """Initialize taxi system tables in the database"""
    
    # Path to database
    db_path = "scum_main.db"
    
    # Path to SQL file
    sql_file = "create_taxi_tables.sql"
    
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
        
        print("SUCCESS: Taxi system tables initialized!")
        print("Database: " + os.path.abspath(db_path))
        
        return True
        
    except Exception as e:
        print("ERROR initializing taxi tables: " + str(e))
        return False

def verify_taxi_tables():
    """Verify that taxi tables were created successfully"""
    
    db_path = "scum_main.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of taxi tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'admin_taxi_%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        print("Found " + str(len(tables)) + " taxi tables:")
        for table in tables:
            print("  - " + table[0])
        
        # Check specific table and count records
        cursor.execute("SELECT COUNT(*) FROM admin_taxi_config")
        config_count = cursor.fetchone()[0]
        print("Taxi configs: " + str(config_count))
        
        cursor.execute("SELECT COUNT(*) FROM admin_taxi_vehicles")
        vehicles_count = cursor.fetchone()[0]
        print("Vehicle types: " + str(vehicles_count))
        
        cursor.execute("SELECT COUNT(*) FROM admin_taxi_zones")
        zones_count = cursor.fetchone()[0]
        print("Taxi zones: " + str(zones_count))
        
        cursor.execute("SELECT COUNT(*) FROM admin_taxi_stops")
        stops_count = cursor.fetchone()[0]
        print("Taxi stops: " + str(stops_count))
        
        cursor.execute("SELECT COUNT(*) FROM admin_taxi_driver_levels")
        levels_count = cursor.fetchone()[0]
        print("Driver levels: " + str(levels_count))
        
        cursor.execute("SELECT COUNT(*) FROM admin_taxi_pricing")
        pricing_count = cursor.fetchone()[0]
        print("Pricing rules: " + str(pricing_count))
        
        conn.close()
        return True
        
    except Exception as e:
        print("ERROR verifying taxi tables: " + str(e))
        return False

if __name__ == "__main__":
    print("Initializing SCUM Bot Taxi System Database...")
    print("=" * 50)
    
    if init_taxi_tables():
        verify_taxi_tables()
        print("Taxi system database initialization complete!")
    else:
        print("Taxi system database initialization failed!")
        sys.exit(1)