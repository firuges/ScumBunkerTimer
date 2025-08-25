"""
Initialize Complete SCUM Bot Database
Creates all tables based on the main bot schema analysis
"""

import sqlite3
import os
import sys

def create_main_database():
    """Create the main database with all bot tables"""
    
    db_path = os.path.join(os.path.dirname(__file__), "scum_main.db")
    db_path = os.path.abspath(db_path)
    
    print(f"Creating SCUM Bot Main Database...")
    print(f"Database path: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Core bot tables from database_v2.py
        print("\n[1/8] Creating core bot tables...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_guild_id TEXT UNIQUE NOT NULL,
                guild_name TEXT,
                server_name TEXT,
                server_ip TEXT,
                server_port INTEGER DEFAULT 7777,
                rcon_password TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bunkers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                bunker_name TEXT NOT NULL,
                location_x REAL,
                location_y REAL,
                location_z REAL,
                is_active INTEGER DEFAULT 1,
                reset_interval_hours INTEGER DEFAULT 24,
                last_reset_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES servers (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                date_used DATE NOT NULL,
                command_used TEXT,
                usage_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(discord_user_id, guild_id, date_used, command_used)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                bunker_id INTEGER,
                notification_type TEXT NOT NULL,
                message TEXT,
                scheduled_time TIMESTAMP,
                sent_at TIMESTAMP,
                is_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bunker_id) REFERENCES bunkers (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                channel_id TEXT,
                is_enabled INTEGER DEFAULT 1,
                notify_minutes_before INTEGER DEFAULT 60,
                message_template TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, notification_type)
            )
        """)
        
        # Fame Points System
        print("\n[2/8] Creating Fame Points tables...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_fame_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                fame_points INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                last_daily_claim DATE,
                weekly_streak INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(discord_user_id, guild_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_fame_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                reward_name TEXT NOT NULL,
                fame_cost INTEGER NOT NULL,
                reward_type TEXT DEFAULT 'item',
                reward_value TEXT DEFAULT '{}',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                usage_limit INTEGER,
                cooldown_hours INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fame_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                reason TEXT,
                reward_id INTEGER,
                admin_user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reward_id) REFERENCES admin_fame_rewards (id)
            )
        """)
        
        # Banking System
        print("\n[3/8] Creating Banking system tables...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_banking_account_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                account_type_name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                initial_balance REAL DEFAULT 0.0,
                interest_rate REAL DEFAULT 0.0,
                minimum_balance REAL DEFAULT 0.0,
                maximum_balance REAL,
                withdrawal_limit REAL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, account_type_name)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_bank_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                account_type_id INTEGER NOT NULL,
                account_number TEXT UNIQUE NOT NULL,
                balance REAL DEFAULT 0.0,
                is_frozen INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_type_id) REFERENCES admin_banking_account_types (id),
                UNIQUE(discord_user_id, guild_id, account_type_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bank_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_before REAL NOT NULL,
                balance_after REAL NOT NULL,
                description TEXT,
                reference_number TEXT,
                admin_user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES user_bank_accounts (id)
            )
        """)
        
        # Taxi System
        print("\n[4/8] Creating Taxi system tables...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_taxi_vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                vehicle_name TEXT NOT NULL,
                vehicle_type TEXT NOT NULL,
                max_passengers INTEGER DEFAULT 4,
                fuel_consumption REAL DEFAULT 1.0,
                speed_multiplier REAL DEFAULT 1.0,
                price_per_km REAL NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS taxi_rides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                vehicle_id INTEGER NOT NULL,
                pickup_location TEXT NOT NULL,
                destination TEXT NOT NULL,
                distance_km REAL NOT NULL,
                price REAL NOT NULL,
                status TEXT DEFAULT 'completed',
                ride_duration_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES admin_taxi_vehicles (id)
            )
        """)
        
        # Mechanic System
        print("\n[5/8] Creating Mechanic system tables...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_mechanic_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                service_name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                base_price REAL NOT NULL,
                description TEXT,
                required_items TEXT DEFAULT '{}',
                service_duration_minutes INTEGER DEFAULT 30,
                skill_requirement INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mechanic_service_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                service_id INTEGER NOT NULL,
                vehicle_type TEXT,
                damage_description TEXT,
                location TEXT,
                status TEXT DEFAULT 'pending',
                price_quoted REAL,
                mechanic_user_id TEXT,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES admin_mechanic_services (id)
            )
        """)
        
        # User Management System (Admin Panel)
        print("\n[6/8] Creating User Management tables...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                module_name TEXT NOT NULL,
                permission_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#6366f1',
                is_system_role INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES admin_roles (id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES admin_permissions (id) ON DELETE CASCADE,
                UNIQUE(role_id, permission_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_user_id TEXT UNIQUE NOT NULL,
                discord_username TEXT NOT NULL,
                discord_discriminator TEXT,
                discord_avatar TEXT,
                email TEXT,
                display_name TEXT,
                role_id INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                is_superuser INTEGER DEFAULT 0,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES admin_roles (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES admin_users (id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                session_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES admin_users (id),
                FOREIGN KEY (session_id) REFERENCES admin_user_sessions (id)
            )
        """)
        
        # Create indexes for performance
        print("\n[7/8] Creating database indexes...")
        
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_usage_user_guild ON daily_usage(discord_user_id, guild_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fame_points_user_guild ON user_fame_points(discord_user_id, guild_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bank_accounts_user_guild ON user_bank_accounts(discord_user_id, guild_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_taxi_rides_user_guild ON taxi_rides(discord_user_id, guild_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mechanic_requests_user_guild ON mechanic_service_requests(discord_user_id, guild_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON admin_audit_logs(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON admin_audit_logs(created_at)")
        except Exception as idx_error:
            print(f"   Warning: Some indexes could not be created: {idx_error}")
        
        # Insert basic data
        print("\n[8/8] Inserting initial data...")
        
        # Default server for testing - skip if tables have different schema
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO servers (discord_guild_id, guild_name, server_name, server_ip)
                VALUES ('123456789', 'Test Guild', 'SCUM Test Server', '127.0.0.1')
            """)
        except sqlite3.Error:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO servers (discord_guild_id, server_name, server_ip)
                    VALUES ('123456789', 'SCUM Test Server', '127.0.0.1')
                """)
            except sqlite3.Error:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO servers (discord_guild_id)
                        VALUES ('123456789')
                    """)
                except sqlite3.Error as e:
                    print(f"   Warning: Could not insert test server data: {e}")
        
        # Default permissions for admin panel
        permissions_data = [
            # Fame module
            ('fame.read', 'Ver Fame Points', 'Ver sistema de puntos de fama', 'fame', 'read'),
            ('fame.write', 'Gestionar Fame Points', 'Crear y editar recompensas de fama', 'fame', 'write'),
            ('fame.admin', 'Administrar Fame Points', 'Control total del sistema de fama', 'fame', 'admin'),
            
            # Banking module
            ('banking.read', 'Ver Banking', 'Ver sistema bancario', 'banking', 'read'),
            ('banking.write', 'Gestionar Banking', 'Crear cuentas y tipos de cuenta', 'banking', 'write'),
            ('banking.admin', 'Administrar Banking', 'Control total del sistema bancario', 'banking', 'admin'),
            
            # Taxi module
            ('taxi.read', 'Ver Taxi', 'Ver sistema de taxi', 'taxi', 'read'),
            ('taxi.write', 'Gestionar Taxi', 'Crear y editar vehículos', 'taxi', 'write'),
            ('taxi.admin', 'Administrar Taxi', 'Control total del sistema de taxi', 'taxi', 'admin'),
            
            # Mechanic module
            ('mechanic.read', 'Ver Mecánico', 'Ver sistema de mecánico', 'mechanic', 'read'),
            ('mechanic.write', 'Gestionar Mecánico', 'Crear y editar servicios', 'mechanic', 'write'),
            ('mechanic.admin', 'Administrar Mecánico', 'Control total del sistema de mecánico', 'mechanic', 'admin'),
            
            # Analytics module
            ('analytics.read', 'Ver Analytics', 'Ver estadísticas y análisis', 'analytics', 'read'),
            
            # Users module
            ('users.read', 'Ver Usuarios', 'Ver usuarios del panel', 'users', 'read'),
            ('users.write', 'Gestionar Usuarios', 'Crear y editar usuarios', 'users', 'write'),
            ('users.admin', 'Administrar Usuarios', 'Control total de usuarios y roles', 'users', 'admin'),
            
            # Logs module
            ('logs.read', 'Ver Logs', 'Ver logs de auditoría', 'logs', 'read'),
            
            # Settings module
            ('settings.read', 'Ver Configuración', 'Ver configuración del sistema', 'settings', 'read'),
            ('settings.write', 'Gestionar Configuración', 'Modificar configuración', 'settings', 'write'),
            ('settings.admin', 'Administrar Configuración', 'Control total de configuración', 'settings', 'admin'),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO admin_permissions 
            (permission_name, display_name, description, module_name, permission_type)
            VALUES (?, ?, ?, ?, ?)
        """, permissions_data)
        
        # Default roles
        roles_data = [
            ('superadmin', 'Super Administrador', 'Acceso completo a todo el sistema', '#ef4444', 1),
            ('admin', 'Administrador', 'Acceso a gestión de sistemas principales', '#f97316', 1),
            ('moderator', 'Moderador', 'Acceso limitado a visualización y moderación', '#eab308', 1),
            ('viewer', 'Visualizador', 'Solo acceso de lectura a estadísticas', '#22c55e', 1),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO admin_roles 
            (role_name, display_name, description, color, is_system_role)
            VALUES (?, ?, ?, ?, ?)
        """, roles_data)
        
        # Assign permissions to roles
        cursor.execute("SELECT id FROM admin_roles WHERE role_name = 'superadmin'")
        superadmin_role_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM admin_permissions")
        all_permission_ids = [row[0] for row in cursor.fetchall()]
        
        # Give superadmin all permissions
        for perm_id in all_permission_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO admin_role_permissions (role_id, permission_id)
                VALUES (?, ?)
            """, (superadmin_role_id, perm_id))
        
        # Create default superadmin user
        cursor.execute("""
            INSERT OR IGNORE INTO admin_users 
            (discord_user_id, discord_username, display_name, role_id, is_superuser)
            VALUES ('123456789012345678', 'admin', 'System Administrator', ?, 1)
        """, (superadmin_role_id,))
        
        conn.commit()
        
        # Verify creation
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        print(f"\n[SUCCESS] Created complete SCUM Bot database!")
        print(f"   Total tables: {len(tables)}")
        
        # Show table counts
        for table in tables:
            table_name = table[0]
            if not table_name.startswith('sqlite_'):
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   - {table_name}: {count} records")
        
        conn.close()
        print(f"\nDatabase path: {db_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating database: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_main_database()
    sys.exit(0 if success else 1)