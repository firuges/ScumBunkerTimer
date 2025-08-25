-- Crear tabla para recompensas de fame points
CREATE TABLE IF NOT EXISTS admin_fame_rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    reward_name TEXT NOT NULL,
    fame_cost INTEGER NOT NULL,
    reward_type TEXT DEFAULT 'item',
    reward_value TEXT DEFAULT '{}', -- JSON
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    max_purchases INTEGER DEFAULT NULL,
    cooldown_hours INTEGER DEFAULT NULL,
    required_role TEXT DEFAULT NULL,
    created_by INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, reward_name)
);

-- Insertar datos de prueba
INSERT OR REPLACE INTO admin_fame_rewards (
    guild_id, reward_name, fame_cost, reward_type, reward_value, description
) VALUES 
('123456789', '🥉 Bronce Reward', 100, 'role', '{"role_id": "123456", "duration": 2628000}', 'Rol bronce por 1 mes'),
('123456789', '🥈 Plata Reward', 250, 'item', '{"item_name": "AK-74", "quantity": 1}', 'Rifle de asalto AK-74'),
('123456789', '🥇 Oro Reward', 500, 'money', '{"amount": 50000, "currency": "dollars"}', '$50,000 en efectivo'),
('123456789', '💎 Platino Reward', 1000, 'vehicle', '{"vehicle": "Hatchback_01", "condition": 100}', 'Vehículo Hatchback'),
('123456789', '🏆 Diamante Reward', 2500, 'custom', '{"type": "base_access", "location": "premium_base"}', 'Acceso a base premium'),
('123456789', '👑 Leyenda Reward', 5000, 'custom', '{"type": "admin_privileges", "duration": 604800}', 'Privilegios admin por 1 semana');

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_fame_rewards_guild ON admin_fame_rewards(guild_id);
CREATE INDEX IF NOT EXISTS idx_fame_rewards_active ON admin_fame_rewards(guild_id, is_active);