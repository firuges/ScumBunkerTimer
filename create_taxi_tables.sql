-- ==========================================
-- TABLAS PARA SISTEMA TAXI - PANEL ADMIN
-- Gestión completa del sistema de taxis del bot SCUM
-- ==========================================

-- Tabla principal de configuración de taxi por guild
CREATE TABLE IF NOT EXISTS admin_taxi_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    taxi_channel_id TEXT, -- Canal principal del taxi
    base_fare REAL DEFAULT 100.0, -- Tarifa base por viaje
    per_km_rate REAL DEFAULT 25.0, -- Tarifa por kilómetro
    commission_percent REAL DEFAULT 10.0, -- Comisión del bot (%)
    max_distance_km REAL DEFAULT 50.0, -- Distancia máxima permitida
    min_fare REAL DEFAULT 50.0, -- Tarifa mínima
    waiting_time_rate REAL DEFAULT 5.0, -- Tarifa por tiempo de espera (por minuto)
    night_multiplier REAL DEFAULT 1.2, -- Multiplicador nocturno
    peak_hours_multiplier REAL DEFAULT 1.5, -- Multiplicador hora pico
    peak_hours_start TEXT DEFAULT '18:00', -- Inicio hora pico
    peak_hours_end TEXT DEFAULT '22:00', -- Fin hora pico
    auto_accept_distance REAL DEFAULT 5.0, -- Distancia para auto-aceptar
    driver_minimum_level INTEGER DEFAULT 1, -- Nivel mínimo de conductor
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER DEFAULT 1,
    UNIQUE(guild_id)
);

-- Tabla de tipos de vehículos
CREATE TABLE IF NOT EXISTS admin_taxi_vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    vehicle_name TEXT NOT NULL, -- 'hatchback', 'suv', 'truck', 'luxury', etc.
    display_name TEXT NOT NULL, -- 'Hatchback Básico', 'SUV Premium', etc.
    description TEXT,
    base_multiplier REAL DEFAULT 1.0, -- Multiplicador de tarifa base
    comfort_multiplier REAL DEFAULT 1.0, -- Multiplicador por comodidad
    speed_multiplier REAL DEFAULT 1.0, -- Multiplicador por velocidad
    capacity_passengers INTEGER DEFAULT 4, -- Capacidad de pasajeros
    fuel_consumption REAL DEFAULT 10.0, -- Consumo de combustible
    maintenance_cost REAL DEFAULT 100.0, -- Costo de mantenimiento
    unlock_level INTEGER DEFAULT 1, -- Nivel requerido para usar
    purchase_cost INTEGER DEFAULT 5000, -- Costo de compra
    emoji TEXT DEFAULT '🚗', -- Emoji para mostrar
    is_active BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE, -- Si es vehículo premium
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, vehicle_name)
);

-- Tabla de zonas PVP/PVE
CREATE TABLE IF NOT EXISTS admin_taxi_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    zone_name TEXT NOT NULL, -- 'safe_zone', 'pvp_zone', 'danger_zone'
    display_name TEXT NOT NULL, -- 'Zona Segura', 'Zona PVP', etc.
    description TEXT,
    zone_type TEXT DEFAULT 'safe', -- 'safe', 'pvp', 'pve', 'danger'
    danger_multiplier REAL DEFAULT 1.0, -- Multiplicador por peligro
    min_driver_level INTEGER DEFAULT 1, -- Nivel mínimo de conductor
    allowed_vehicles TEXT DEFAULT 'all', -- JSON array de vehículos permitidos
    restricted_hours TEXT, -- JSON de horarios restringidos
    coordinate_bounds TEXT, -- JSON con coordenadas del área
    warning_message TEXT, -- Mensaje de advertencia
    requires_confirmation BOOLEAN DEFAULT FALSE, -- Si requiere confirmación
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, zone_name)
);

-- Tabla de paradas de taxi configurables
CREATE TABLE IF NOT EXISTS admin_taxi_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    stop_name TEXT NOT NULL, -- 'bunker_a1', 'city_center', 'airport'
    display_name TEXT NOT NULL, -- 'Bunker A1', 'Centro Ciudad', etc.
    description TEXT,
    coordinate_x REAL NOT NULL, -- Coordenada X en el mapa
    coordinate_y REAL NOT NULL, -- Coordenada Y en el mapa
    coordinate_z REAL DEFAULT 0.0, -- Coordenada Z (altura)
    zone_id INTEGER, -- FK a admin_taxi_zones
    is_pickup_point BOOLEAN DEFAULT TRUE, -- Si es punto de recogida
    is_dropoff_point BOOLEAN DEFAULT TRUE, -- Si es punto de destino
    popularity_bonus REAL DEFAULT 0.0, -- Bonus por popularidad
    waiting_area_size REAL DEFAULT 50.0, -- Tamaño del área de espera (metros)
    landmark_type TEXT DEFAULT 'general', -- 'bunker', 'city', 'poi', 'base'
    emoji TEXT DEFAULT '📍', -- Emoji para mostrar
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES admin_taxi_zones(id),
    UNIQUE(guild_id, stop_name)
);

-- Tabla de niveles de conductor
CREATE TABLE IF NOT EXISTS admin_taxi_driver_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    level_name TEXT NOT NULL, -- 'Novato', 'Experto', 'Maestro'
    description TEXT,
    required_trips INTEGER DEFAULT 0, -- Viajes requeridos
    required_distance REAL DEFAULT 0.0, -- Distancia total requerida
    earnings_multiplier REAL DEFAULT 1.0, -- Multiplicador de ganancias
    tip_multiplier REAL DEFAULT 1.0, -- Multiplicador de propinas
    unlock_vehicles TEXT DEFAULT '[]', -- JSON array de vehículos desbloqueados
    unlock_zones TEXT DEFAULT '[]', -- JSON array de zonas desbloqueadas
    special_perks TEXT DEFAULT '{}', -- JSON de beneficios especiales
    badge_emoji TEXT DEFAULT '🚗', -- Emoji de insignia
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, level)
);

-- Tabla de tarifas especiales y promociones
CREATE TABLE IF NOT EXISTS admin_taxi_pricing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    pricing_name TEXT NOT NULL, -- 'weekend_discount', 'holiday_surge'
    display_name TEXT NOT NULL, -- 'Descuento Fin de Semana'
    description TEXT,
    pricing_type TEXT DEFAULT 'multiplier', -- 'multiplier', 'fixed_discount', 'percentage_discount'
    multiplier_value REAL DEFAULT 1.0, -- Valor del multiplicador
    discount_amount REAL DEFAULT 0.0, -- Monto de descuento
    min_distance REAL DEFAULT 0.0, -- Distancia mínima para aplicar
    max_distance REAL DEFAULT 999999.0, -- Distancia máxima
    applicable_zones TEXT DEFAULT '[]', -- JSON array de zonas aplicables
    applicable_vehicles TEXT DEFAULT '[]', -- JSON array de vehículos aplicables
    start_time TEXT, -- Hora de inicio (HH:MM)
    end_time TEXT, -- Hora de fin (HH:MM)
    days_of_week TEXT DEFAULT '[]', -- JSON array de días (0=domingo, 6=sábado)
    start_date DATE, -- Fecha de inicio
    end_date DATE, -- Fecha de fin
    priority INTEGER DEFAULT 1, -- Prioridad (mayor número = mayor prioridad)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, pricing_name)
);

-- Insertar datos de ejemplo para testing
INSERT OR REPLACE INTO admin_taxi_config (
    guild_id, taxi_channel_id, base_fare, per_km_rate, commission_percent,
    max_distance_km, min_fare, waiting_time_rate, night_multiplier
) VALUES (
    '123456789', '987654321', 150.0, 30.0, 12.0,
    75.0, 75.0, 8.0, 1.3
);

-- Vehículos de ejemplo
INSERT OR REPLACE INTO admin_taxi_vehicles (
    guild_id, vehicle_name, display_name, description, base_multiplier,
    comfort_multiplier, capacity_passengers, purchase_cost, emoji, is_premium
) VALUES 
('123456789', 'hatchback', '🚗 Hatchback Básico', 'Vehículo económico ideal para distancias cortas', 0.8, 0.9, 4, 3000, '🚗', FALSE),
('123456789', 'suv', '🚙 SUV Premium', 'Vehículo cómodo para grupos y largas distancias', 1.2, 1.4, 6, 8000, '🚙', TRUE),
('123456789', 'truck', '🚚 Camioneta Cargo', 'Ideal para transportar equipamiento pesado', 1.5, 1.0, 3, 12000, '🚚', FALSE),
('123456789', 'luxury', '🏎️ Vehículo de Lujo', 'Máxima comodidad y velocidad', 2.0, 2.2, 2, 25000, '🏎️', TRUE);

-- Zonas de ejemplo
INSERT OR REPLACE INTO admin_taxi_zones (
    guild_id, zone_name, display_name, description, zone_type, danger_multiplier, min_driver_level
) VALUES 
('123456789', 'safe_zone', '🟢 Zona Segura', 'Área protegida sin riesgo de PVP', 'safe', 1.0, 1),
('123456789', 'pvp_zone', '🔴 Zona PVP', 'Área de combate jugador vs jugador - PELIGROSO', 'pvp', 1.8, 3),
('123456789', 'neutral_zone', '🟡 Zona Neutral', 'Área mixta con riesgo moderado', 'neutral', 1.3, 2),
('123456789', 'bunker_zone', '🏰 Zona de Bunkers', 'Área con bunkers activos - Alta actividad', 'pve', 1.5, 2);

-- Paradas de ejemplo
INSERT OR REPLACE INTO admin_taxi_stops (
    guild_id, stop_name, display_name, description, coordinate_x, coordinate_y,
    is_pickup_point, is_dropoff_point, landmark_type, emoji
) VALUES 
('123456789', 'spawn_beach', '🏖️ Playa de Spawn', 'Punto de aparición principal', 0.0, 0.0, TRUE, TRUE, 'spawn', '🏖️'),
('123456789', 'bunker_a1', '🏰 Bunker A1', 'Bunker sector A1 - Alta seguridad', 1500.0, 2300.0, TRUE, TRUE, 'bunker', '🏰'),
('123456789', 'city_center', '🏙️ Centro Ciudad', 'Centro urbano principal', 800.0, 1200.0, TRUE, TRUE, 'city', '🏙️'),
('123456789', 'military_base', '🪖 Base Militar', 'Complejo militar - Zona restringida', 2500.0, 3000.0, TRUE, FALSE, 'military', '🪖');

-- Niveles de conductor de ejemplo
INSERT OR REPLACE INTO admin_taxi_driver_levels (
    guild_id, level, level_name, description, required_trips, required_distance,
    earnings_multiplier, tip_multiplier, badge_emoji
) VALUES 
('123456789', 1, '🆕 Conductor Novato', 'Recién comenzando en el mundo del taxi', 0, 0.0, 1.0, 1.0, '🆕'),
('123456789', 2, '⭐ Conductor Experimentado', 'Ya conoce las rutas básicas', 25, 500.0, 1.1, 1.15, '⭐'),
('123456789', 3, '🌟 Conductor Experto', 'Domina rutas complejas y zonas peligrosas', 75, 1500.0, 1.25, 1.3, '🌟'),
('123456789', 4, '👑 Maestro del Volante', 'Leyenda del transporte en SCUM', 200, 5000.0, 1.5, 1.6, '👑');

-- Tarifas especiales de ejemplo
INSERT OR REPLACE INTO admin_taxi_pricing (
    guild_id, pricing_name, display_name, description, pricing_type,
    multiplier_value, start_time, end_time, priority
) VALUES 
('123456789', 'weekend_bonus', '🎉 Bonus Fin de Semana', 'Tarifas aumentadas los fines de semana', 'multiplier', 1.25, '00:00', '23:59', 2),
('123456789', 'night_shift', '🌙 Tarifa Nocturna', 'Recargo por servicio nocturno', 'multiplier', 1.4, '22:00', '06:00', 3),
('123456789', 'bunker_rush', '⚡ Rush de Bunkers', 'Tarifa especial para viajes a bunkers', 'multiplier', 1.6, '19:00', '23:00', 1);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_taxi_config_guild ON admin_taxi_config(guild_id);
CREATE INDEX IF NOT EXISTS idx_taxi_vehicles_guild ON admin_taxi_vehicles(guild_id, is_active);
CREATE INDEX IF NOT EXISTS idx_taxi_zones_guild ON admin_taxi_zones(guild_id, is_active);
CREATE INDEX IF NOT EXISTS idx_taxi_stops_guild ON admin_taxi_stops(guild_id, is_active);
CREATE INDEX IF NOT EXISTS idx_taxi_driver_levels_guild ON admin_taxi_driver_levels(guild_id, level);
CREATE INDEX IF NOT EXISTS idx_taxi_pricing_guild ON admin_taxi_pricing(guild_id, is_active);