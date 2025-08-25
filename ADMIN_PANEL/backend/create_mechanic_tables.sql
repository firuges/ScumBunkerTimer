-- ========================================
-- SCUM Bot - Admin Panel Mechanic System
-- Database Schema for Mechanic/Insurance System
-- ========================================

-- 1. Servicios de Mecánico (Seguros de Vehículos)
CREATE TABLE IF NOT EXISTS mechanic_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id TEXT UNIQUE NOT NULL,
    vehicle_insurance_id TEXT,
    service_type TEXT NOT NULL DEFAULT 'insurance',
    description TEXT,
    cost INTEGER NOT NULL,
    mechanic_discord_id TEXT,
    client_discord_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    vehicle_id TEXT NOT NULL,
    vehicle_type TEXT NOT NULL,
    vehicle_location TEXT NOT NULL,
    payment_method TEXT NOT NULL DEFAULT 'ingame',
    ingame_name TEXT NOT NULL,
    client_display_name TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    mechanic_assigned_at TEXT,
    completed_at TEXT
);

-- 2. Mecánicos Registrados
CREATE TABLE IF NOT EXISTS registered_mechanics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT NOT NULL,
    discord_guild_id TEXT NOT NULL,
    ingame_name TEXT NOT NULL,
    registered_by TEXT NOT NULL,
    registered_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT DEFAULT 'active',
    specialties TEXT DEFAULT 'insurance,repairs,maintenance',
    experience_level TEXT DEFAULT 'beginner',
    total_services INTEGER DEFAULT 0,
    rating REAL DEFAULT 5.0,
    UNIQUE(discord_id, discord_guild_id)
);

-- 3. Preferencias de Mecánicos
CREATE TABLE IF NOT EXISTS mechanic_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT NOT NULL,
    discord_guild_id TEXT NOT NULL,
    receive_notifications BOOLEAN DEFAULT TRUE,
    notification_types TEXT DEFAULT 'all',
    work_schedule TEXT DEFAULT 'anytime',
    preferred_services TEXT DEFAULT 'insurance',
    max_concurrent_jobs INTEGER DEFAULT 5,
    auto_accept_price_limit INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(discord_id, discord_guild_id)
);

-- 4. Historial de Seguros (Auditoría)
CREATE TABLE IF NOT EXISTS insurance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id TEXT NOT NULL,
    client_discord_id TEXT NOT NULL,
    mechanic_discord_id TEXT,
    guild_id TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    vehicle_type TEXT NOT NULL,
    cost INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL,
    action TEXT NOT NULL,
    action_by TEXT NOT NULL,
    action_at TEXT NOT NULL DEFAULT (datetime('now')),
    notes TEXT,
    previous_status TEXT
);

-- 5. Precios de Vehículos Personalizados
CREATE TABLE IF NOT EXISTS vehicle_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    vehicle_type TEXT NOT NULL,
    price INTEGER NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active BOOLEAN DEFAULT TRUE,
    price_multiplier REAL DEFAULT 1.0,
    pvp_surcharge_percent INTEGER DEFAULT 50,
    UNIQUE(guild_id, vehicle_type)
);

-- 6. Configuración del Sistema Mecánico (NUEVA para Admin Panel)
CREATE TABLE IF NOT EXISTS admin_mechanic_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL UNIQUE,
    mechanic_channel_id TEXT,
    notification_channel_id TEXT,
    auto_assign_mechanics BOOLEAN DEFAULT FALSE,
    require_payment_confirmation BOOLEAN DEFAULT TRUE,
    max_pending_requests_per_user INTEGER DEFAULT 3,
    service_timeout_hours INTEGER DEFAULT 24,
    pvp_zone_surcharge_percent INTEGER DEFAULT 50,
    default_vehicle_insurance_rate REAL DEFAULT 1000.0,
    commission_percent REAL DEFAULT 10.0,
    min_mechanic_level INTEGER DEFAULT 1,
    max_concurrent_services INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_by INTEGER
);

-- ========================================
-- DATOS DE EJEMPLO PARA TESTING
-- ========================================

-- Configuración base para testing
INSERT OR REPLACE INTO admin_mechanic_config (
    guild_id, mechanic_channel_id, notification_channel_id,
    auto_assign_mechanics, require_payment_confirmation,
    max_pending_requests_per_user, service_timeout_hours,
    pvp_zone_surcharge_percent, default_vehicle_insurance_rate,
    commission_percent, min_mechanic_level, max_concurrent_services,
    is_active, updated_by
) VALUES (
    '123456789', '1234567890123456789', '1234567890123456790',
    0, 1,  -- auto_assign: false, require_payment: true
    3, 24, -- max 3 requests per user, 24h timeout
    50, 1000.0, -- 50% PvP surcharge, $1000 base insurance
    10.0, 1, 10, -- 10% commission, level 1 min, max 10 concurrent
    1, 1   -- active, updated by admin user 1
);

-- Mecánicos de ejemplo
INSERT OR REPLACE INTO registered_mechanics (
    discord_id, discord_guild_id, ingame_name, registered_by,
    status, specialties, experience_level, total_services, rating
) VALUES 
('987654321098765432', '123456789', 'MechMaster_Pro', '123456789012345678', 
 'active', 'insurance,repairs,maintenance', 'expert', 150, 4.8),
('876543210987654321', '123456789', 'FixItFast', '123456789012345678', 
 'active', 'insurance,repairs', 'intermediate', 85, 4.6),
('765432109876543210', '123456789', 'VehicleDoc', '123456789012345678', 
 'active', 'insurance,maintenance,custom', 'advanced', 120, 4.9),
('654321098765432109', '123456789', 'QuickRepair', '123456789012345678', 
 'active', 'insurance,emergency', 'beginner', 25, 4.2);

-- Precios personalizados por tipo de vehículo
INSERT OR REPLACE INTO vehicle_prices (
    guild_id, vehicle_type, price, updated_by, 
    price_multiplier, pvp_surcharge_percent
) VALUES 
('123456789', 'motocicleta', 500, '123456789012345678', 1.0, 50),
('123456789', 'atv', 750, '123456789012345678', 1.0, 50),
('123456789', 'automovil', 1000, '123456789012345678', 1.0, 50),
('123456789', 'suv', 1500, '123456789012345678', 1.0, 50),
('123456789', 'camion', 2000, '123456789012345678', 1.0, 50),
('123456789', 'camioneta', 1750, '123456789012345678', 1.0, 50),
('123456789', 'helicoptero', 5000, '123456789012345678', 1.0, 75),
('123456789', 'avion', 8000, '123456789012345678', 1.0, 75),
('123456789', 'barco', 3000, '123456789012345678', 1.0, 25);

-- Preferencias de mecánicos
INSERT OR REPLACE INTO mechanic_preferences (
    discord_id, discord_guild_id, receive_notifications, notification_types,
    work_schedule, preferred_services, max_concurrent_jobs, auto_accept_price_limit
) VALUES 
('987654321098765432', '123456789', 1, 'all', 'anytime', 'insurance,repairs', 8, 2000),
('876543210987654321', '123456789', 1, 'high_priority', '09:00-18:00', 'insurance', 5, 1500),
('765432109876543210', '123456789', 1, 'all', '14:00-02:00', 'insurance,maintenance', 10, 0),
('654321098765432109', '123456789', 1, 'insurance_only', 'weekends', 'insurance', 3, 1000);

-- Servicios de ejemplo (historial)
INSERT OR REPLACE INTO mechanic_services (
    service_id, vehicle_insurance_id, service_type, description,
    cost, mechanic_discord_id, client_discord_id, guild_id,
    status, vehicle_id, vehicle_type, vehicle_location,
    payment_method, ingame_name, client_display_name,
    mechanic_assigned_at, completed_at
) VALUES 
('MS_001_2025', 'INS_VEH_001', 'insurance', 'Seguro completo vehículo SUV',
 1500, '987654321098765432', '111222333444555666', '123456789',
 'completed', 'VEH_SUV_001', 'suv', 'PVE',
 'ingame', 'PlayerOne', 'PlayerOne#1234',
 datetime('now', '-2 days'), datetime('now', '-2 days', '+3 hours')),
('MS_002_2025', 'INS_VEH_002', 'insurance', 'Seguro motocicleta zona PVP',
 750, '876543210987654321', '222333444555666777', '123456789',
 'active', 'VEH_MOTO_002', 'motocicleta', 'PVP',
 'discord', 'SpeedRider', 'SpeedRider#5678',
 datetime('now', '-1 days'), NULL),
('MS_003_2025', 'INS_VEH_003', 'insurance', 'Seguro camión transporte',
 2000, '765432109876543210', '333444555666777888', '123456789',
 'pending_confirmation', 'VEH_TRUCK_003', 'camion', 'PVE',
 'ingame', 'TruckDriver', 'TruckDriver#9012',
 datetime('now', '-6 hours'), NULL);