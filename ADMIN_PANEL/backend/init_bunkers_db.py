#!/usr/bin/env python3
"""
Initialize bunkers admin database tables
"""

import sqlite3
import os

def create_bunkers_admin_tables():
    """Create admin tables for bunkers management"""
    
    # Connect to main database
    db_path = "scum_main.db"
    if not os.path.exists(db_path):
        print("[ERROR] Database file not found. Run init_main_database.py first.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating bunkers admin tables...")
    
    try:
        # Admin Bunker Servers Configuration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_bunker_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                max_bunkers INTEGER DEFAULT 100,
                is_active BOOLEAN DEFAULT 1,
                default_notification_channels TEXT, -- JSON array of channel IDs
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL,
                UNIQUE(guild_id, name)
            )
        """)
        
        # Admin Bunker Sectors Configuration  
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_bunker_sectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                sector TEXT NOT NULL,
                name TEXT NOT NULL,
                coordinates TEXT,
                description TEXT,
                default_duration_hours INTEGER DEFAULT 24,
                notification_enabled BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL,
                UNIQUE(guild_id, sector)
            )
        """)
        
        # Admin Notification Configurations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_bunker_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                server_name TEXT,
                bunker_sector TEXT, -- NULL for all sectors
                notification_type TEXT NOT NULL, -- new, warning_30, warning_15, warning_5, expired
                channel_id TEXT NOT NULL,
                minutes_before INTEGER NOT NULL,
                message_template TEXT,
                role_mention TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL
            )
        """)
        
        # Bunker System Configuration per Guild
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_bunker_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL UNIQUE,
                enabled BOOLEAN DEFAULT 1,
                max_bunkers_per_user INTEGER DEFAULT 5,
                max_daily_registrations INTEGER DEFAULT 50,
                auto_cleanup_expired BOOLEAN DEFAULT 1,
                cleanup_after_hours INTEGER DEFAULT 24,
                require_confirmation BOOLEAN DEFAULT 0,
                allow_anonymous_registration BOOLEAN DEFAULT 1,
                premium_features_enabled BOOLEAN DEFAULT 0,
                default_bunker_duration INTEGER DEFAULT 24, -- hours
                notification_settings TEXT, -- JSON config
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL
            )
        """)
        
        # Bunker Alerts/Notifications Queue
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_bunker_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                server_name TEXT NOT NULL,
                bunker_sector TEXT NOT NULL,
                bunker_id INTEGER,
                notification_type TEXT NOT NULL,
                scheduled_time TIMESTAMP NOT NULL,
                sent BOOLEAN DEFAULT 0,
                sent_time TIMESTAMP,
                channel_id TEXT NOT NULL,
                message_content TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bunker_id) REFERENCES bunkers(id) ON DELETE CASCADE
            )
        """)
        
        # Bunker Usage Statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_bunker_usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                date DATE NOT NULL,
                registrations_count INTEGER DEFAULT 0,
                total_duration_hours INTEGER DEFAULT 0,
                most_used_sector TEXT,
                premium_user BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, date)
            )
        """)
        
        print("[OK] Created admin_bunker_servers table")
        print("[OK] Created admin_bunker_sectors table")  
        print("[OK] Created admin_bunker_notifications table")
        print("[OK] Created admin_bunker_config table")
        print("[OK] Created admin_bunker_alerts table")
        print("[OK] Created admin_bunker_usage_stats table")
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bunker_servers_guild ON admin_bunker_servers(guild_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bunker_sectors_guild ON admin_bunker_sectors(guild_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bunker_notifications_guild ON admin_bunker_notifications(guild_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bunker_alerts_scheduled ON admin_bunker_alerts(scheduled_time, sent)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bunker_usage_date ON admin_bunker_usage_stats(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bunker_usage_guild_user ON admin_bunker_usage_stats(guild_id, user_id)")
        
        print("[OK] Created database indexes")
        
        # Insert some default data
        print("\nInserting default bunkers configuration...")
        
        # Default server for testing
        cursor.execute("""
            INSERT OR IGNORE INTO admin_bunker_servers 
            (guild_id, name, display_name, description, max_bunkers, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "DEFAULT_GUILD",
            "Default", 
            "Default Server",
            "Default SCUM server for bunker tracking",
            100,
            "system"
        ))
        
        # Common bunker sectors
        default_sectors = [
            ("A1", "Alpha Sector A1", "0,0"),
            ("A2", "Alpha Sector A2", "100,0"),
            ("B1", "Bravo Sector B1", "0,100"),
            ("B2", "Bravo Sector B2", "100,100"),
            ("C1", "Charlie Sector C1", "200,200"),
            ("C2", "Charlie Sector C2", "300,200"),
            ("D1", "Delta Sector D1", "0,200"),
            ("D2", "Delta Sector D2", "100,200"),
        ]
        
        for sector, name, coords in default_sectors:
            cursor.execute("""
                INSERT OR IGNORE INTO admin_bunker_sectors
                (guild_id, sector, name, coordinates, default_duration_hours, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "DEFAULT_GUILD",
                sector,
                name,
                coords,
                24,
                "system"
            ))
        
        # Default bunker configuration
        cursor.execute("""
            INSERT OR IGNORE INTO admin_bunker_config
            (guild_id, enabled, max_bunkers_per_user, max_daily_registrations, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "DEFAULT_GUILD",
            1,
            5,
            50,
            "system"
        ))
        
        print("[OK] Inserted default servers and sectors")
        
        conn.commit()
        print("\nBunkers admin database initialized successfully!")
        print("\nSummary:")
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM admin_bunker_servers")
        servers_count = cursor.fetchone()[0]
        print(f"   Servers configured: {servers_count}")
        
        cursor.execute("SELECT COUNT(*) FROM admin_bunker_sectors") 
        sectors_count = cursor.fetchone()[0]
        print(f"   Sectors configured: {sectors_count}")
        
        cursor.execute("SELECT COUNT(*) FROM admin_bunker_config")
        configs_count = cursor.fetchone()[0]
        print(f"   Guild configurations: {configs_count}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating bunkers admin tables: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("BUNKERS ADMIN DATABASE SETUP")
    print("=" * 50)
    
    success = create_bunkers_admin_tables()
    
    if success:
        print(f"\n[SUCCESS] Setup completed successfully!")
        print(f"   Database: scum_main.db")
        print(f"   Tables: admin_bunker_* series")
        print(f"\nYou can now use the bunkers module in the admin panel!")
    else:
        print(f"\n[ERROR] Setup failed!")
        print(f"   Check the error messages above")
        exit(1)