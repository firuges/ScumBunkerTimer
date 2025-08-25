-- User Management System Tables
-- Admin Panel users, roles, permissions and audit trail

-- Admin users table - Users who can access the admin panel
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_user_id TEXT UNIQUE NOT NULL,
    discord_username TEXT NOT NULL,
    discord_discriminator TEXT,
    discord_avatar TEXT,
    email TEXT,
    display_name TEXT,
    role_id INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES admin_roles(id)
);

-- Admin roles table - Role definitions
CREATE TABLE IF NOT EXISTS admin_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#6366f1', -- Indigo color
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin permissions table - Available permissions
CREATE TABLE IF NOT EXISTS admin_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permission_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    module_name TEXT NOT NULL, -- fame, banking, taxi, mechanic, analytics, users, logs, settings
    permission_type TEXT NOT NULL DEFAULT 'read', -- read, write, delete, admin
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Role permissions table - Which permissions each role has
CREATE TABLE IF NOT EXISTS admin_role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER,
    FOREIGN KEY (role_id) REFERENCES admin_roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES admin_permissions(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES admin_users(id),
    UNIQUE(role_id, permission_id)
);

-- User sessions table - Track login sessions
CREATE TABLE IF NOT EXISTS admin_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    discord_access_token TEXT,
    discord_refresh_token TEXT,
    expires_at TIMESTAMP NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- Audit log table - Track all admin actions
CREATE TABLE IF NOT EXISTS admin_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL, -- create, update, delete, login, logout, etc.
    resource_type TEXT NOT NULL, -- user, role, fame_reward, banking_config, etc.
    resource_id TEXT,
    old_values TEXT, -- JSON
    new_values TEXT, -- JSON
    ip_address TEXT,
    user_agent TEXT,
    session_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES admin_users(id),
    FOREIGN KEY (session_id) REFERENCES admin_sessions(id)
);

-- Insert default roles
INSERT OR IGNORE INTO admin_roles (id, role_name, display_name, description, is_system_role) VALUES
(1, 'viewer', 'Viewer', 'Can only view data, no modifications allowed', TRUE),
(2, 'moderator', 'Moderator', 'Can manage most systems except users and critical settings', TRUE),
(3, 'administrator', 'Administrator', 'Full access to all systems including user management', TRUE),
(4, 'superuser', 'Super User', 'Full system access with audit trail exemptions', TRUE);

-- Insert default permissions
INSERT OR IGNORE INTO admin_permissions (permission_name, display_name, description, module_name, permission_type) VALUES
-- Fame Points permissions
('fame.read', 'View Fame Rewards', 'Can view fame rewards and statistics', 'fame', 'read'),
('fame.write', 'Manage Fame Rewards', 'Can create and update fame rewards', 'fame', 'write'),
('fame.delete', 'Delete Fame Rewards', 'Can delete fame rewards', 'fame', 'delete'),

-- Banking permissions  
('banking.read', 'View Banking Config', 'Can view banking configuration and accounts', 'banking', 'read'),
('banking.write', 'Manage Banking', 'Can modify banking settings and account types', 'banking', 'write'),
('banking.admin', 'Banking Admin', 'Full banking system administration', 'banking', 'admin'),

-- Taxi permissions
('taxi.read', 'View Taxi System', 'Can view taxi configuration and metrics', 'taxi', 'read'),
('taxi.write', 'Manage Taxi System', 'Can modify taxi vehicles, zones, and pricing', 'taxi', 'write'),
('taxi.admin', 'Taxi Admin', 'Full taxi system administration', 'taxi', 'admin'),

-- Mechanic permissions
('mechanic.read', 'View Mechanic System', 'Can view mechanic configuration and services', 'mechanic', 'read'),
('mechanic.write', 'Manage Mechanics', 'Can manage mechanics and service pricing', 'mechanic', 'write'),
('mechanic.admin', 'Mechanic Admin', 'Full mechanic system administration', 'mechanic', 'admin'),

-- Analytics permissions
('analytics.read', 'View Analytics', 'Can view system analytics and reports', 'analytics', 'read'),
('analytics.admin', 'Analytics Admin', 'Can access detailed analytics and performance data', 'analytics', 'admin'),

-- User Management permissions
('users.read', 'View Users', 'Can view user list and roles', 'users', 'read'),
('users.write', 'Manage Users', 'Can create and modify user accounts', 'users', 'write'),
('users.admin', 'User Admin', 'Full user management including role assignments', 'users', 'admin'),

-- Audit Logs permissions
('logs.read', 'View Audit Logs', 'Can view system audit logs', 'logs', 'read'),
('logs.admin', 'Logs Admin', 'Can export and manage audit logs', 'logs', 'admin'),

-- Settings permissions
('settings.read', 'View Settings', 'Can view system settings', 'settings', 'read'),
('settings.write', 'Manage Settings', 'Can modify system configuration', 'settings', 'write'),
('settings.admin', 'Settings Admin', 'Full system settings administration', 'settings', 'admin');

-- Assign permissions to default roles

-- Viewer role (ID: 1) - Read only permissions
INSERT OR IGNORE INTO admin_role_permissions (role_id, permission_id) 
SELECT 1, id FROM admin_permissions WHERE permission_type = 'read';

-- Moderator role (ID: 2) - Read and write permissions (except users, logs, settings)
INSERT OR IGNORE INTO admin_role_permissions (role_id, permission_id)
SELECT 2, id FROM admin_permissions 
WHERE module_name IN ('fame', 'banking', 'taxi', 'mechanic', 'analytics') 
AND permission_type IN ('read', 'write');

-- Administrator role (ID: 3) - All permissions except superuser-level settings
INSERT OR IGNORE INTO admin_role_permissions (role_id, permission_id)
SELECT 3, id FROM admin_permissions WHERE permission_name != 'settings.admin';

-- Superuser role (ID: 4) - All permissions
INSERT OR IGNORE INTO admin_role_permissions (role_id, permission_id)
SELECT 4, id FROM admin_permissions;

-- Create a default superuser (update with real Discord user ID when needed)
INSERT OR IGNORE INTO admin_users (
    discord_user_id, 
    discord_username, 
    display_name, 
    role_id, 
    is_superuser
) VALUES (
    '123456789012345678', 
    'admin', 
    'System Administrator', 
    4, 
    TRUE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_admin_users_discord_id ON admin_users(discord_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_token ON admin_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_user ON admin_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_user ON admin_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_created ON admin_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_role_permissions_role ON admin_role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_admin_permissions_module ON admin_permissions(module_name);