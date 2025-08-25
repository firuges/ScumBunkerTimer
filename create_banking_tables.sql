-- ==========================================
-- TABLAS PARA SISTEMA BANCARIO - PANEL ADMIN
-- Gestión completa del sistema bancario del bot SCUM
-- ==========================================

-- Tabla principal de configuración bancaria por guild
CREATE TABLE IF NOT EXISTS admin_banking_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    bank_channel_id TEXT, -- Canal principal del banco
    welcome_bonus INTEGER DEFAULT 7500, -- Bonus inicial para nuevos usuarios
    daily_bonus INTEGER DEFAULT 500, -- Bonus diario
    min_balance INTEGER DEFAULT 0, -- Balance mínimo permitido
    max_balance INTEGER DEFAULT 1000000, -- Balance máximo
    transfer_fee_percent REAL DEFAULT 2.5, -- Comisión por transferencias (%)
    min_transfer_amount INTEGER DEFAULT 100, -- Mínimo para transferir
    max_transfer_amount INTEGER DEFAULT 50000, -- Máximo por transferencia
    max_daily_transfers INTEGER DEFAULT 10, -- Máximo transferencias por día
    overdraft_enabled BOOLEAN DEFAULT FALSE, -- Permitir números negativos
    overdraft_limit INTEGER DEFAULT 0, -- Límite de sobregiro
    interest_rate REAL DEFAULT 0.1, -- Tasa de interés diaria (%)
    bank_hours_start TEXT DEFAULT '08:00', -- Hora apertura banco
    bank_hours_end TEXT DEFAULT '20:00', -- Hora cierre banco
    weekend_enabled BOOLEAN DEFAULT TRUE, -- Banco abierto fines de semana
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER DEFAULT 1,
    UNIQUE(guild_id)
);

-- Tabla de tipos de cuenta bancaria
CREATE TABLE IF NOT EXISTS admin_banking_account_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    account_type_name TEXT NOT NULL, -- 'basic', 'premium', 'vip', etc.
    display_name TEXT NOT NULL, -- 'Cuenta Básica', 'Cuenta Premium', etc.
    description TEXT,
    min_balance INTEGER DEFAULT 0,
    max_balance INTEGER DEFAULT 100000,
    daily_limit INTEGER DEFAULT 10000,
    transfer_fee_percent REAL DEFAULT 2.5,
    monthly_fee INTEGER DEFAULT 0, -- Cuota mensual de mantenimiento
    interest_rate REAL DEFAULT 0.1, -- Tasa de interés especial
    overdraft_limit INTEGER DEFAULT 0,
    required_role TEXT, -- Rol requerido para esta cuenta
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, account_type_name)
);

-- Tabla de comisiones y tarifas configurables
CREATE TABLE IF NOT EXISTS admin_banking_fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    fee_type TEXT NOT NULL, -- 'transfer', 'withdrawal', 'deposit', 'maintenance'
    fee_name TEXT NOT NULL, -- Nombre descriptivo
    fee_method TEXT DEFAULT 'percentage', -- 'percentage', 'fixed', 'tiered'
    fee_value REAL NOT NULL, -- Valor de la comisión
    min_amount INTEGER DEFAULT 0, -- Monto mínimo para aplicar
    max_amount INTEGER DEFAULT NULL, -- Monto máximo
    applies_to TEXT DEFAULT 'all', -- 'all', 'basic', 'premium', etc.
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, fee_type, fee_name)
);

-- Tabla de configuración de canales
CREATE TABLE IF NOT EXISTS admin_banking_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_type TEXT NOT NULL, -- 'main', 'logs', 'announcements', 'support'
    channel_id TEXT NOT NULL,
    channel_name TEXT, -- Nombre descriptivo
    auto_delete_messages BOOLEAN DEFAULT FALSE, -- Auto-limpiar mensajes
    delete_after_minutes INTEGER DEFAULT 60, -- Minutos antes de limpiar
    embed_color TEXT DEFAULT '#00FF00', -- Color de embeds en este canal
    ping_role TEXT, -- Rol a mencionar en notificaciones
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, channel_type)
);

-- Tabla de límites por usuario/rol
CREATE TABLE IF NOT EXISTS admin_banking_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    limit_type TEXT NOT NULL, -- 'user', 'role', 'global'
    target_id TEXT, -- user_id o role_id (NULL para global)
    daily_deposit_limit INTEGER DEFAULT 10000,
    daily_withdrawal_limit INTEGER DEFAULT 5000,
    daily_transfer_limit INTEGER DEFAULT 3000,
    max_transactions_per_hour INTEGER DEFAULT 10,
    max_account_balance INTEGER DEFAULT 100000,
    cooldown_between_transfers INTEGER DEFAULT 300, -- Segundos
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, limit_type, target_id)
);

-- Tabla de notificaciones y alertas
CREATE TABLE IF NOT EXISTS admin_banking_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    notification_type TEXT NOT NULL, -- 'low_balance', 'large_transaction', 'daily_summary'
    trigger_amount INTEGER DEFAULT 1000, -- Monto que dispara la notificación
    message_template TEXT NOT NULL, -- Template del mensaje
    channel_id TEXT, -- Canal donde enviar
    ping_role TEXT, -- Rol a mencionar
    embed_enabled BOOLEAN DEFAULT TRUE,
    embed_color TEXT DEFAULT '#FF6B35',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, notification_type)
);

-- Tabla de horarios especiales (feriados, eventos)
CREATE TABLE IF NOT EXISTS admin_banking_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    schedule_name TEXT NOT NULL, -- 'Christmas', 'Server Event', etc.
    schedule_type TEXT DEFAULT 'holiday', -- 'holiday', 'event', 'maintenance'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_bank_closed BOOLEAN DEFAULT FALSE, -- Si el banco está cerrado
    special_hours_start TEXT, -- Horario especial apertura
    special_hours_end TEXT, -- Horario especial cierre
    bonus_multiplier REAL DEFAULT 1.0, -- Multiplicador de bonos
    fee_multiplier REAL DEFAULT 1.0, -- Multiplicador de comisiones
    message TEXT, -- Mensaje especial para mostrar
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar datos de ejemplo para testing
INSERT OR REPLACE INTO admin_banking_config (
    guild_id, bank_channel_id, welcome_bonus, daily_bonus, 
    transfer_fee_percent, min_transfer_amount, max_transfer_amount
) VALUES (
    '123456789', '987654321', 10000, 750, 
    2.0, 50, 25000
);

-- Tipos de cuenta de ejemplo
INSERT OR REPLACE INTO admin_banking_account_types (
    guild_id, account_type_name, display_name, description,
    max_balance, daily_limit, transfer_fee_percent, interest_rate
) VALUES 
('123456789', 'basic', '🏦 Cuenta Básica', 'Cuenta estándar para todos los usuarios', 50000, 5000, 3.0, 0.05),
('123456789', 'premium', '💎 Cuenta Premium', 'Cuenta con beneficios adicionales', 200000, 15000, 1.5, 0.15),
('123456789', 'vip', '👑 Cuenta VIP', 'Cuenta exclusiva para miembros VIP', 500000, 50000, 0.5, 0.25);

-- Comisiones de ejemplo
INSERT OR REPLACE INTO admin_banking_fees (
    guild_id, fee_type, fee_name, fee_method, fee_value, min_amount
) VALUES 
('123456789', 'transfer', 'Transferencia Estándar', 'percentage', 2.5, 100),
('123456789', 'transfer', 'Transferencia Grande', 'percentage', 1.5, 10000),
('123456789', 'withdrawal', 'Retiro ATM', 'fixed', 50, 0),
('123456789', 'maintenance', 'Cuota Mensual Premium', 'fixed', 500, 0);

-- Canales de ejemplo
INSERT OR REPLACE INTO admin_banking_channels (
    guild_id, channel_type, channel_id, channel_name, embed_color
) VALUES 
('123456789', 'main', '111111111', '🏦│banco-principal', '#00D4AA'),
('123456789', 'logs', '222222222', '📊│banco-logs', '#FFA500'),
('123456789', 'announcements', '333333333', '📢│banco-anuncios', '#FF6B35');

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_banking_config_guild ON admin_banking_config(guild_id);
CREATE INDEX IF NOT EXISTS idx_banking_account_types_guild ON admin_banking_account_types(guild_id, is_active);
CREATE INDEX IF NOT EXISTS idx_banking_fees_guild ON admin_banking_fees(guild_id, is_active);
CREATE INDEX IF NOT EXISTS idx_banking_channels_guild ON admin_banking_channels(guild_id);
CREATE INDEX IF NOT EXISTS idx_banking_limits_guild ON admin_banking_limits(guild_id, limit_type);
CREATE INDEX IF NOT EXISTS idx_banking_notifications_guild ON admin_banking_notifications(guild_id, is_active);