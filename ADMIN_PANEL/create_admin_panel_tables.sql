-- ==========================================
-- TABLAS PARA PANEL ADMINISTRATIVO WEB
-- Sistema de gestión administrativa para SCUM Bot
-- ==========================================

-- Tabla de usuarios administrativos
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    discriminator TEXT,
    avatar_url TEXT,
    email TEXT,
    guild_permissions TEXT, -- JSON: {guild_id: [permissions]}
    global_permissions TEXT, -- JSON: [permissions] para super-admins
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    session_token TEXT,
    refresh_token TEXT,
    is_super_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de sesiones administrativas
CREATE TABLE IF NOT EXISTS admin_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    guild_id TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    device_info TEXT, -- JSON: navegador, OS, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- Tabla de logs de auditoría
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    guild_id TEXT NOT NULL,
    action TEXT NOT NULL, -- 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT'
    resource_type TEXT NOT NULL, -- 'fame_rewards', 'vehicle_prices', 'taxi_config', etc.
    resource_id TEXT,
    resource_name TEXT, -- Nombre descriptivo del recurso
    old_values TEXT, -- JSON: valores anteriores
    new_values TEXT, -- JSON: valores nuevos
    ip_address TEXT,
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE SET NULL
);

-- Tabla de configuraciones del panel
CREATE TABLE IF NOT EXISTS admin_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    category TEXT NOT NULL, -- 'general', 'fame_rewards', 'taxi', 'banking', etc.
    setting_key TEXT NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type TEXT DEFAULT 'string', -- 'string', 'json', 'boolean', 'integer', 'float'
    display_name TEXT, -- Nombre amigable para mostrar en UI
    description TEXT, -- Descripción de la configuración
    is_sensitive BOOLEAN DEFAULT FALSE, -- Para datos que requieren encriptación extra
    validation_rules TEXT, -- JSON: reglas de validación
    updated_by INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, category, setting_key),
    FOREIGN KEY (updated_by) REFERENCES admin_users(id)
);

-- Tabla de respaldos automáticos
CREATE TABLE IF NOT EXISTS admin_backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    backup_type TEXT NOT NULL, -- 'manual', 'automatic', 'scheduled', 'pre_update'
    backup_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    backup_data TEXT, -- JSON: metadata sobre qué se respaldó
    checksum TEXT, -- Para verificar integridad
    is_restore_point BOOLEAN DEFAULT FALSE,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP, -- Para limpieza automática
    FOREIGN KEY (created_by) REFERENCES admin_users(id) ON DELETE SET NULL
);

-- Tabla de templates de configuración
CREATE TABLE IF NOT EXISTS admin_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    template_category TEXT NOT NULL, -- 'fame_rewards', 'taxi_complete', 'basic_setup', etc.
    description TEXT,
    template_data TEXT NOT NULL, -- JSON: configuración completa
    preview_image TEXT, -- URL o path a imagen de preview
    tags TEXT, -- JSON: ['pvp', 'pve', 'roleplay', etc.]
    version TEXT DEFAULT '1.0',
    is_official BOOLEAN DEFAULT FALSE, -- Templates oficiales del sistema
    is_public BOOLEAN DEFAULT FALSE, -- Compartible entre servidores
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    downloads_count INTEGER DEFAULT 0,
    rating REAL DEFAULT 0.0,
    FOREIGN KEY (created_by) REFERENCES admin_users(id)
);

-- Tabla de notificaciones del panel
CREATE TABLE IF NOT EXISTS admin_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    guild_id TEXT,
    notification_type TEXT NOT NULL, -- 'info', 'warning', 'error', 'success'
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    action_url TEXT, -- URL para acción relacionada
    action_label TEXT, -- Etiqueta del botón de acción
    is_read BOOLEAN DEFAULT FALSE,
    is_global BOOLEAN DEFAULT FALSE, -- Para todos los admins del sistema
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- Tabla de métricas y analytics
CREATE TABLE IF NOT EXISTS admin_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    metric_type TEXT NOT NULL, -- 'command_usage', 'user_activity', 'feature_usage', etc.
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_data TEXT, -- JSON: datos adicionales
    time_period TEXT NOT NULL, -- 'hourly', 'daily', 'weekly', 'monthly'
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(guild_id, metric_type, recorded_at)
);

-- Tabla de tareas en background
CREATE TABLE IF NOT EXISTS admin_background_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    task_type TEXT NOT NULL, -- 'backup', 'sync', 'analytics', 'cleanup'
    guild_id TEXT,
    user_id INTEGER,
    status TEXT DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    progress INTEGER DEFAULT 0, -- Porcentaje de progreso (0-100)
    task_data TEXT, -- JSON: parámetros de la tarea
    result_data TEXT, -- JSON: resultado de la tarea
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE SET NULL
);

-- Tabla de configuración de automation rules
CREATE TABLE IF NOT EXISTS admin_automation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    description TEXT,
    trigger_type TEXT NOT NULL, -- 'schedule', 'event', 'condition'
    trigger_config TEXT NOT NULL, -- JSON: configuración del trigger
    condition_config TEXT, -- JSON: condiciones adicionales
    action_config TEXT NOT NULL, -- JSON: acciones a ejecutar
    is_active BOOLEAN DEFAULT TRUE,
    last_executed TIMESTAMP,
    execution_count INTEGER DEFAULT 0,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES admin_users(id)
);

-- Tabla de webhooks externos
CREATE TABLE IF NOT EXISTS admin_webhooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    webhook_name TEXT NOT NULL,
    webhook_url TEXT NOT NULL,
    webhook_secret TEXT, -- Para validar requests
    event_types TEXT NOT NULL, -- JSON: ['user_registered', 'fame_claimed', etc.]
    is_active BOOLEAN DEFAULT TRUE,
    retry_count INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 30,
    last_used TIMESTAMP,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES admin_users(id)
);

-- ==========================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ==========================================

-- Índices para admin_users
CREATE INDEX IF NOT EXISTS idx_admin_users_discord_id ON admin_users(discord_id);
CREATE INDEX IF NOT EXISTS idx_admin_users_active ON admin_users(is_active);

-- Índices para admin_sessions
CREATE INDEX IF NOT EXISTS idx_admin_sessions_token ON admin_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_user ON admin_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_guild ON admin_sessions(guild_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires ON admin_sessions(expires_at);

-- Índices para admin_audit_logs
CREATE INDEX IF NOT EXISTS idx_admin_audit_user_guild ON admin_audit_logs(user_id, guild_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_resource ON admin_audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_audit_guild_action ON admin_audit_logs(guild_id, action);

-- Índices para admin_settings
CREATE INDEX IF NOT EXISTS idx_admin_settings_guild_category ON admin_settings(guild_id, category);
CREATE INDEX IF NOT EXISTS idx_admin_settings_updated ON admin_settings(updated_at DESC);

-- Índices para admin_notifications
CREATE INDEX IF NOT EXISTS idx_admin_notifications_user ON admin_notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_admin_notifications_guild ON admin_notifications(guild_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_notifications_expires ON admin_notifications(expires_at);

-- Índices para admin_analytics
CREATE INDEX IF NOT EXISTS idx_admin_analytics_guild_type ON admin_analytics(guild_id, metric_type);
CREATE INDEX IF NOT EXISTS idx_admin_analytics_recorded ON admin_analytics(recorded_at DESC);

-- ==========================================
-- DATOS INICIALES Y CONFIGURACIÓN
-- ==========================================

-- Configuraciones por defecto del panel
INSERT OR IGNORE INTO admin_settings (guild_id, category, setting_key, setting_value, setting_type, display_name, description, updated_by) 
VALUES 
('default', 'general', 'session_timeout', '3600', 'integer', 'Timeout de Sesión', 'Tiempo en segundos antes de que expire una sesión inactiva', 1),
('default', 'general', 'max_concurrent_sessions', '5', 'integer', 'Sesiones Concurrentes', 'Número máximo de sesiones activas por usuario', 1),
('default', 'general', 'enable_audit_logs', 'true', 'boolean', 'Logs de Auditoría', 'Registrar todas las acciones administrativas', 1),
('default', 'general', 'auto_backup_frequency', '24', 'integer', 'Frecuencia Respaldo Auto', 'Horas entre respaldos automáticos', 1),
('default', 'general', 'backup_retention_days', '30', 'integer', 'Retención de Respaldos', 'Días para mantener respaldos automáticos', 1),
('default', 'security', 'require_2fa', 'false', 'boolean', 'Requerir 2FA', 'Autenticación de dos factores obligatoria', 1),
('default', 'security', 'allowed_ip_ranges', '[]', 'json', 'Rangos IP Permitidos', 'Lista de rangos IP con acceso al panel (vacío = todos)', 1),
('default', 'ui', 'theme', 'auto', 'string', 'Tema Visual', 'Tema del panel: light, dark, auto', 1),
('default', 'ui', 'items_per_page', '25', 'integer', 'Items por Página', 'Número de elementos a mostrar en tablas', 1),
('default', 'notifications', 'enable_email', 'false', 'boolean', 'Notificaciones Email', 'Enviar notificaciones importantes por email', 1),
('default', 'notifications', 'enable_discord_dm', 'true', 'boolean', 'Notificaciones Discord DM', 'Enviar notificaciones por mensaje directo en Discord', 1);

-- Templates oficiales básicos
INSERT OR IGNORE INTO admin_templates (template_name, template_category, description, template_data, is_official, is_public, created_by)
VALUES 
('Servidor PVP Básico', 'complete_setup', 'Configuración completa para servidor PVP con todas las funcionalidades habilitadas', 
'{"fame_rewards":{"enabled":true,"values":[100,250,500,1000,2500]},"taxi":{"enabled":true,"pvp_zones":true},"banking":{"enabled":true,"welcome_bonus":7500},"mechanics":{"enabled":true,"pvp_markup":25}}', 
true, true, 1),
('Servidor PVE Roleplay', 'complete_setup', 'Configuración orientada a roleplay con enfoque en cooperación', 
'{"fame_rewards":{"enabled":true,"values":[50,150,300,750,1500]},"taxi":{"enabled":true,"pvp_zones":false},"banking":{"enabled":true,"welcome_bonus":10000},"mechanics":{"enabled":true,"pvp_markup":0}}', 
true, true, 1),
('Solo Sistema de Fama', 'fame_rewards', 'Únicamente sistema de puntos de fama con configuración estándar', 
'{"fame_rewards":{"enabled":true,"values":[100,250,500,1000,2000,5000],"rewards":{"100":"🥉 Bronce","250":"🥈 Plata","500":"🥇 Oro","1000":"💎 Platino","2000":"🏆 Diamante","5000":"👑 Leyenda"}}}', 
true, true, 1);

-- Notificación de bienvenida para nuevos administradores
INSERT OR IGNORE INTO admin_notifications (guild_id, notification_type, title, message, is_global)
VALUES 
('default', 'info', '¡Bienvenido al Panel Administrativo!', 
'Gracias por usar el panel administrativo de SCUM Bot. Aquí puedes gestionar todas las configuraciones de tu servidor de forma sencilla. Te recomendamos comenzar con el Dashboard para familiarizarte con las funcionalidades disponibles.', 
true);

-- ==========================================
-- VISTAS ÚTILES PARA REPORTING
-- ==========================================

-- Vista de actividad administrativa por guild
CREATE VIEW IF NOT EXISTS admin_activity_summary AS
SELECT 
    guild_id,
    DATE(created_at) as activity_date,
    COUNT(*) as total_actions,
    COUNT(DISTINCT user_id) as active_admins,
    COUNT(CASE WHEN action = 'CREATE' THEN 1 END) as creates,
    COUNT(CASE WHEN action = 'UPDATE' THEN 1 END) as updates,
    COUNT(CASE WHEN action = 'DELETE' THEN 1 END) as deletes
FROM admin_audit_logs 
WHERE success = TRUE
GROUP BY guild_id, DATE(created_at);

-- Vista de sesiones activas
CREATE VIEW IF NOT EXISTS admin_active_sessions AS
SELECT 
    s.id,
    s.user_id,
    u.username,
    u.discord_id,
    s.guild_id,
    s.ip_address,
    s.created_at,
    s.last_activity,
    s.expires_at,
    (s.expires_at > datetime('now')) as is_valid
FROM admin_sessions s
JOIN admin_users u ON s.user_id = u.id
WHERE s.is_active = TRUE;

-- Vista de métricas diarias por guild
CREATE VIEW IF NOT EXISTS admin_daily_metrics AS
SELECT 
    guild_id,
    DATE(recorded_at) as metric_date,
    metric_type,
    metric_name,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    COUNT(*) as data_points
FROM admin_analytics
WHERE time_period = 'daily'
GROUP BY guild_id, DATE(recorded_at), metric_type, metric_name;

-- ==========================================
-- TRIGGERS PARA MANTENIMIENTO AUTOMÁTICO
-- ==========================================

-- Trigger para actualizar updated_at en admin_users
CREATE TRIGGER IF NOT EXISTS update_admin_users_timestamp 
AFTER UPDATE ON admin_users
BEGIN
    UPDATE admin_users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para limpiar sesiones expiradas automáticamente
CREATE TRIGGER IF NOT EXISTS cleanup_expired_sessions
AFTER INSERT ON admin_sessions
BEGIN
    DELETE FROM admin_sessions 
    WHERE expires_at < datetime('now') 
    AND is_active = FALSE;
END;

-- Trigger para limpiar notificaciones expiradas
CREATE TRIGGER IF NOT EXISTS cleanup_expired_notifications
AFTER INSERT ON admin_notifications
BEGIN
    DELETE FROM admin_notifications 
    WHERE expires_at IS NOT NULL 
    AND expires_at < datetime('now');
END;

-- ==========================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ==========================================

/*
NOTAS DE IMPLEMENTACIÓN:

1. SEGURIDAD:
   - Todos los tokens de sesión deben ser hasheados antes del almacenamiento
   - Los campos sensitive en admin_settings requieren encriptación adicional
   - Las contraseñas nunca se almacenan (solo OAuth Discord)
   - Los logs de auditoría son inmutables una vez creados

2. PERFORMANCE:
   - Los índices están optimizados para consultas frecuentes
   - Las vistas materializadas pueden ser útiles para analytics pesados
   - Considerar particionado por fecha para tablas de logs grandes

3. MANTENIMIENTO:
   - Implementar job de limpieza diaria para datos expirados
   - Rotación automática de logs después de 90 días
   - Compresión de respaldos antiguos

4. ESCALABILIDAD:
   - La estructura soporta múltiples guilds por usuario
   - Templates compartibles entre servidores
   - Sistema de webhooks para integraciones externas

5. BACKUP STRATEGY:
   - Respaldos automáticos diarios de configuraciones críticas
   - Respaldos manuales antes de cambios importantes
   - Puntos de restauración marcados por los administradores
*/