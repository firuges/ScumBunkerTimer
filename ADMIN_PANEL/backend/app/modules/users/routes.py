"""
User Management Module - FastAPI Routes
Sistema completo de gestión de usuarios, roles y permisos
"""

import sqlite3
import os
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from .models import (
    User, UserCreate, UserUpdate, UserSummary, UserFilter, UserPermissions,
    Role, RoleCreate, RoleUpdate, RoleSummary,
    Permission, PermissionCreate, PermissionsByModule,
    AuditLogEntry, AuditLogCreate, AuditLogFilter,
    SystemStats, ModuleName, PermissionType, AuditAction
)

router = APIRouter()

# Database path (5 levels up from this file)
db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "scum_main.db")

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(db_path)

def log_audit_action(user_id: Optional[int], action: str, resource_type: str, 
                    resource_id: Optional[str] = None, old_values: Optional[dict] = None, 
                    new_values: Optional[dict] = None):
    """Log an audit action"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO admin_audit_log 
            (user_id, action, resource_type, resource_id, old_values, new_values, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, action, resource_type, resource_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging audit action: {e}")

# Users Endpoints

@router.get("/users", response_model=List[UserSummary])
async def get_users(
    search: Optional[str] = Query(None, description="Search in username or display name"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get list of admin users with filtering and pagination"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        where_conditions = ["1=1"]
        params = []
        
        if search:
            where_conditions.append("(u.discord_username LIKE ? OR u.display_name LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        if role_id:
            where_conditions.append("u.role_id = ?")
            params.append(role_id)
        
        if is_active is not None:
            where_conditions.append("u.is_active = ?")
            params.append(is_active)
        
        where_clause = " AND ".join(where_conditions)
        
        cursor.execute(f"""
            SELECT u.id, u.discord_username, u.display_name, u.is_active, u.is_superuser, 
                   u.last_login, r.role_name, r.display_name as role_display_name
            FROM admin_users u
            JOIN admin_roles r ON u.role_id = r.id
            WHERE {where_clause}
            ORDER BY u.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        users = []
        for row in cursor.fetchall():
            users.append(UserSummary(
                id=row[0],
                discord_username=row[1],
                display_name=row[2],
                is_active=bool(row[3]),
                is_superuser=bool(row[4]),
                last_login=datetime.fromisoformat(row[5]) if row[5] else None,
                role_name=row[6],
                role_display_name=row[7]
            ))
        
        conn.close()
        return users
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting users: {str(e)}")

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get specific user by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user details
        cursor.execute("""
            SELECT u.id, u.discord_user_id, u.discord_username, u.discord_discriminator,
                   u.discord_avatar, u.email, u.display_name, u.role_id, u.is_active,
                   u.is_superuser, u.last_login, u.login_count, u.created_at, u.updated_at,
                   r.role_name, r.display_name as role_display_name, r.description as role_description,
                   r.color, r.is_system_role
            FROM admin_users u
            JOIN admin_roles r ON u.role_id = r.id
            WHERE u.id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user permissions
        cursor.execute("""
            SELECT p.id, p.permission_name, p.display_name, p.description, 
                   p.module_name, p.permission_type, p.created_at
            FROM admin_permissions p
            JOIN admin_role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = ?
            ORDER BY p.module_name, p.permission_name
        """, (row[7],))  # role_id
        
        permissions = []
        for perm_row in cursor.fetchall():
            permissions.append(Permission(
                id=perm_row[0],
                permission_name=perm_row[1],
                display_name=perm_row[2],
                description=perm_row[3],
                module_name=perm_row[4],
                permission_type=perm_row[5],
                created_at=datetime.fromisoformat(perm_row[6]) if perm_row[6] else None
            ))
        
        # Create role object
        role = Role(
            id=row[7],
            role_name=row[14],
            display_name=row[15],
            description=row[16],
            color=row[17],
            is_system_role=bool(row[18]),
            permissions=permissions
        )
        
        # Create user object
        user = User(
            id=row[0],
            discord_user_id=row[1],
            discord_username=row[2],
            discord_discriminator=row[3],
            discord_avatar=row[4],
            email=row[5],
            display_name=row[6],
            role_id=row[7],
            role=role,
            is_active=bool(row[8]),
            is_superuser=bool(row[9]),
            last_login=datetime.fromisoformat(row[10]) if row[10] else None,
            login_count=row[11],
            permissions=permissions,
            created_at=datetime.fromisoformat(row[12]) if row[12] else None,
            updated_at=datetime.fromisoformat(row[13]) if row[13] else None
        )
        
        conn.close()
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

@router.post("/users", response_model=User)
async def create_user(user_data: UserCreate):
    """Create new admin user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM admin_users WHERE discord_user_id = ?", (user_data.discord_user_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="User with this Discord ID already exists")
        
        # Verify role exists
        cursor.execute("SELECT id FROM admin_roles WHERE id = ?", (user_data.role_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Role not found")
        
        # Create user
        cursor.execute("""
            INSERT INTO admin_users 
            (discord_user_id, discord_username, discord_discriminator, discord_avatar, 
             email, display_name, role_id, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data.discord_user_id,
            user_data.discord_username,
            user_data.discord_discriminator,
            user_data.discord_avatar,
            user_data.email,
            user_data.display_name,
            user_data.role_id,
            True,
            datetime.now()
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        # Log audit action
        log_audit_action(None, "create", "user", str(user_id), None, user_data.dict())
        
        conn.close()
        
        # Return created user
        return await get_user(user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_data: UserUpdate):
    """Update existing user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current user data for audit
        cursor.execute("SELECT * FROM admin_users WHERE id = ?", (user_id,))
        current_user = cursor.fetchone()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build update query
        update_fields = []
        params = []
        
        if user_data.discord_username is not None:
            update_fields.append("discord_username = ?")
            params.append(user_data.discord_username)
        
        if user_data.discord_discriminator is not None:
            update_fields.append("discord_discriminator = ?")
            params.append(user_data.discord_discriminator)
        
        if user_data.discord_avatar is not None:
            update_fields.append("discord_avatar = ?")
            params.append(user_data.discord_avatar)
        
        if user_data.email is not None:
            update_fields.append("email = ?")
            params.append(user_data.email)
        
        if user_data.display_name is not None:
            update_fields.append("display_name = ?")
            params.append(user_data.display_name)
        
        if user_data.role_id is not None:
            # Verify role exists
            cursor.execute("SELECT id FROM admin_roles WHERE id = ?", (user_data.role_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Role not found")
            update_fields.append("role_id = ?")
            params.append(user_data.role_id)
        
        if user_data.is_active is not None:
            update_fields.append("is_active = ?")
            params.append(user_data.is_active)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Add updated_at and user_id to params
        update_fields.append("updated_at = ?")
        params.extend([datetime.now(), user_id])
        
        # Update user
        cursor.execute(f"""
            UPDATE admin_users 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """, params)
        
        conn.commit()
        
        # Log audit action
        log_audit_action(None, "update", "user", str(user_id), 
                        {"old": dict(zip(['id', 'discord_user_id', 'discord_username'], current_user[:3]))},
                        user_data.dict(exclude_unset=True))
        
        conn.close()
        
        # Return updated user
        return await get_user(user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete user (soft delete - set inactive)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT discord_username FROM admin_users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Soft delete (set inactive)
        cursor.execute("""
            UPDATE admin_users 
            SET is_active = FALSE, updated_at = ?
            WHERE id = ?
        """, (datetime.now(), user_id))
        
        conn.commit()
        
        # Log audit action
        log_audit_action(None, "delete", "user", str(user_id))
        
        conn.close()
        
        return {"message": f"User {user[0]} deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

# Roles Endpoints

@router.get("/roles", response_model=List[RoleSummary])
async def get_roles():
    """Get all roles with user counts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.id, r.role_name, r.display_name, r.color, r.is_system_role,
                   COUNT(DISTINCT rp.permission_id) as permission_count,
                   COUNT(DISTINCT u.id) as user_count
            FROM admin_roles r
            LEFT JOIN admin_role_permissions rp ON r.id = rp.role_id
            LEFT JOIN admin_users u ON r.id = u.role_id AND u.is_active = TRUE
            GROUP BY r.id, r.role_name, r.display_name, r.color, r.is_system_role
            ORDER BY r.id
        """)
        
        roles = []
        for row in cursor.fetchall():
            roles.append(RoleSummary(
                id=row[0],
                role_name=row[1],
                display_name=row[2],
                color=row[3],
                is_system_role=bool(row[4]),
                permission_count=row[5],
                user_count=row[6]
            ))
        
        conn.close()
        return roles
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting roles: {str(e)}")

@router.get("/permissions", response_model=List[PermissionsByModule])
async def get_permissions():
    """Get all permissions grouped by module"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, permission_name, display_name, description, module_name, permission_type, created_at
            FROM admin_permissions
            ORDER BY module_name, permission_name
        """)
        
        permissions_by_module = {}
        for row in cursor.fetchall():
            module_name = row[4]
            permission = Permission(
                id=row[0],
                permission_name=row[1],
                display_name=row[2],
                description=row[3],
                module_name=module_name,
                permission_type=row[5],
                created_at=datetime.fromisoformat(row[6]) if row[6] else None
            )
            
            if module_name not in permissions_by_module:
                permissions_by_module[module_name] = []
            permissions_by_module[module_name].append(permission)
        
        result = []
        module_display_names = {
            "fame": "Fame Points System",
            "banking": "Banking System", 
            "taxi": "Taxi System",
            "mechanic": "Mechanic System",
            "analytics": "Analytics Dashboard",
            "users": "User Management",
            "logs": "Audit Logs",
            "settings": "System Settings"
        }
        
        for module_name, permissions in permissions_by_module.items():
            result.append(PermissionsByModule(
                module_name=module_name,
                module_display_name=module_display_names.get(module_name, module_name.title()),
                permissions=permissions
            ))
        
        conn.close()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting permissions: {str(e)}")

@router.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM admin_users")
        total_users = cursor.fetchone()[0]
        
        # Active users
        cursor.execute("SELECT COUNT(*) FROM admin_users WHERE is_active = TRUE")
        active_users = cursor.fetchone()[0]
        
        # Total roles
        cursor.execute("SELECT COUNT(*) FROM admin_roles")
        total_roles = cursor.fetchone()[0]
        
        # Total permissions
        cursor.execute("SELECT COUNT(*) FROM admin_permissions")
        total_permissions = cursor.fetchone()[0]
        
        # Recent logins (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM admin_users 
            WHERE last_login > datetime('now', '-1 day')
        """)
        recent_logins = cursor.fetchone()[0]
        
        # Active sessions
        cursor.execute("""
            SELECT COUNT(*) FROM admin_sessions 
            WHERE is_active = TRUE AND expires_at > datetime('now')
        """)
        pending_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        return SystemStats(
            total_users=total_users,
            active_users=active_users,
            total_roles=total_roles,
            total_permissions=total_permissions,
            recent_logins=recent_logins,
            pending_sessions=pending_sessions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system stats: {str(e)}")

@router.get("/audit-logs", response_model=List[AuditLogEntry])
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(50, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get audit logs with filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        where_conditions = ["1=1"]
        params = []
        
        if user_id:
            where_conditions.append("al.user_id = ?")
            params.append(user_id)
        
        if action:
            where_conditions.append("al.action = ?")
            params.append(action)
        
        if resource_type:
            where_conditions.append("al.resource_type = ?")
            params.append(resource_type)
        
        where_clause = " AND ".join(where_conditions)
        
        cursor.execute(f"""
            SELECT al.id, al.user_id, al.action, al.resource_type, al.resource_id,
                   al.old_values, al.new_values, al.ip_address, al.user_agent,
                   al.session_id, al.created_at, u.discord_username
            FROM admin_audit_log al
            LEFT JOIN admin_users u ON al.user_id = u.id
            WHERE {where_clause}
            ORDER BY al.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        logs = []
        for row in cursor.fetchall():
            logs.append(AuditLogEntry(
                id=row[0],
                user_id=row[1],
                action=row[2],
                resource_type=row[3],
                resource_id=row[4],
                old_values=json.loads(row[5]) if row[5] else None,
                new_values=json.loads(row[6]) if row[6] else None,
                ip_address=row[7],
                user_agent=row[8],
                session_id=row[9],
                created_at=datetime.fromisoformat(row[10]) if row[10] else None
            ))
        
        conn.close()
        return logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting audit logs: {str(e)}")

@router.get("/users/{user_id}/permissions", response_model=UserPermissions)
async def get_user_permissions(user_id: int):
    """Get detailed permissions for a specific user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user and role info
        cursor.execute("""
            SELECT u.role_id, r.role_name
            FROM admin_users u
            JOIN admin_roles r ON u.role_id = r.id
            WHERE u.id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        role_id, role_name = row
        
        # Get permissions
        cursor.execute("""
            SELECT p.id, p.permission_name, p.display_name, p.description, 
                   p.module_name, p.permission_type, p.created_at
            FROM admin_permissions p
            JOIN admin_role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = ?
            ORDER BY p.module_name, p.permission_name
        """, (role_id,))
        
        permissions_list = []
        permissions_by_module = {}
        
        for row in cursor.fetchall():
            permission = Permission(
                id=row[0],
                permission_name=row[1],
                display_name=row[2],
                description=row[3],
                module_name=row[4],
                permission_type=row[5],
                created_at=datetime.fromisoformat(row[6]) if row[6] else None
            )
            
            permissions_list.append(permission.permission_name)
            
            module_name = row[4]
            if module_name not in permissions_by_module:
                permissions_by_module[module_name] = []
            permissions_by_module[module_name].append(permission)
        
        # Format modules
        module_display_names = {
            "fame": "Fame Points System",
            "banking": "Banking System", 
            "taxi": "Taxi System",
            "mechanic": "Mechanic System",
            "analytics": "Analytics Dashboard",
            "users": "User Management",
            "logs": "Audit Logs",
            "settings": "System Settings"
        }
        
        modules = []
        for module_name, permissions in permissions_by_module.items():
            modules.append(PermissionsByModule(
                module_name=module_name,
                module_display_name=module_display_names.get(module_name, module_name.title()),
                permissions=permissions
            ))
        
        conn.close()
        
        return UserPermissions(
            user_id=user_id,
            role_id=role_id,
            role_name=role_name,
            permissions=permissions_list,
            modules=modules
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user permissions: {str(e)}")