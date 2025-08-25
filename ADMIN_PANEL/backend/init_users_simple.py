"""
Initialize User Management System Database
Creates tables and inserts sample data for testing
"""

import sqlite3
import os
import sys

def init_users_database():
    """Initialize the users management database"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), "..", "scum_main.db")
    db_path = os.path.abspath(db_path)
    
    print(f"Initializing Users Management Database...")
    print(f"Database path: {db_path}")
    
    try:
        # Read SQL file
        sql_file = os.path.join(os.path.dirname(__file__), "create_users_tables.sql")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Execute SQL
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute all statements
        cursor.executescript(sql_content)
        
        # Verify creation
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'admin_%' 
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        print(f"\n[SUCCESS] Created {len(tables)} user management tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   - {table[0]}: {count} records")
        
        # Show roles created
        cursor.execute("SELECT role_name, display_name, description FROM admin_roles ORDER BY id")
        roles = cursor.fetchall()
        print(f"\n[ROLES] Created {len(roles)} default roles:")
        for role in roles:
            print(f"   - {role[0]}: {role[1]} - {role[2]}")
        
        # Show permissions created
        cursor.execute("SELECT COUNT(*) FROM admin_permissions")
        permission_count = cursor.fetchone()[0]
        print(f"\n[PERMISSIONS] Created {permission_count} permissions across all modules")
        
        # Show permission breakdown by module
        cursor.execute("""
            SELECT module_name, COUNT(*) 
            FROM admin_permissions 
            GROUP BY module_name 
            ORDER BY module_name
        """)
        modules = cursor.fetchall()
        for module in modules:
            print(f"   - {module[0]}: {module[1]} permissions")
        
        # Show role-permission assignments
        cursor.execute("""
            SELECT r.role_name, COUNT(rp.permission_id) as permission_count
            FROM admin_roles r
            LEFT JOIN admin_role_permissions rp ON r.id = rp.role_id
            GROUP BY r.id, r.role_name
            ORDER BY r.id
        """)
        role_perms = cursor.fetchall()
        print(f"\n[ASSIGNMENTS] Role-Permission assignments:")
        for role_perm in role_perms:
            print(f"   - {role_perm[0]}: {role_perm[1]} permissions")
        
        # Show default admin user
        cursor.execute("""
            SELECT u.discord_username, u.display_name, r.role_name, u.is_superuser
            FROM admin_users u
            JOIN admin_roles r ON u.role_id = r.id
        """)
        users = cursor.fetchall()
        print(f"\n[USERS] Created {len(users)} default users:")
        for user in users:
            superuser_flag = " (SUPERUSER)" if user[3] else ""
            print(f"   - {user[0]} ({user[1]}) - Role: {user[2]}{superuser_flag}")
        
        conn.commit()
        conn.close()
        
        print(f"\n[COMPLETE] Users Management System initialized successfully!")
        print(f"Database: {db_path}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error initializing users database: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_users_database()
    sys.exit(0 if success else 1)