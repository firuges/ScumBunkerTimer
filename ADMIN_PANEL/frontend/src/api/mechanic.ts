/**
 * API Client para el Sistema Mecánico
 * Maneja todas las operaciones CRUD del módulo mecánico
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ================================
// INTERFACES TYPESCRIPT
// ================================

export interface MechanicConfig {
  id: number;
  guild_id: string;
  mechanic_channel_id?: string;
  notification_channel_id?: string;
  auto_assign_mechanics: boolean;
  require_payment_confirmation: boolean;
  max_pending_requests_per_user: number;
  service_timeout_hours: number;
  pvp_zone_surcharge_percent: number;
  default_vehicle_insurance_rate: number;
  commission_percent: number;
  min_mechanic_level: number;
  max_concurrent_services: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  updated_by?: number;
}

export interface MechanicConfigUpdate {
  mechanic_channel_id?: string;
  notification_channel_id?: string;
  auto_assign_mechanics: boolean;
  require_payment_confirmation: boolean;
  max_pending_requests_per_user: number;
  service_timeout_hours: number;
  pvp_zone_surcharge_percent: number;
  default_vehicle_insurance_rate: number;
  commission_percent: number;
  min_mechanic_level: number;
  max_concurrent_services: number;
  is_active: boolean;
}

export interface RegisteredMechanic {
  id: number;
  discord_id: string;
  discord_guild_id: string;
  ingame_name: string;
  registered_by: string;
  registered_at: string;
  status: string;
  specialties: string;
  experience_level: string;
  total_services: number;
  rating: number;
}

export interface MechanicCreate {
  discord_id: string;
  discord_guild_id: string;
  ingame_name: string;
  registered_by: string;
  status?: string;
  specialties?: string;
  experience_level?: string;
}

export interface MechanicUpdate {
  ingame_name?: string;
  status?: string;
  specialties?: string;
  experience_level?: string;
}

export interface MechanicService {
  id: number;
  service_id: string;
  vehicle_insurance_id?: string;
  service_type: string;
  description?: string;
  cost: number;
  mechanic_discord_id?: string;
  client_discord_id: string;
  guild_id: string;
  status: string;
  vehicle_id: string;
  vehicle_type: string;
  vehicle_location: string;
  payment_method: string;
  ingame_name: string;
  client_display_name?: string;
  created_at: string;
  updated_at: string;
  mechanic_assigned_at?: string;
  completed_at?: string;
}

export interface ServiceCreate {
  service_id: string;
  vehicle_insurance_id?: string;
  service_type?: string;
  description?: string;
  cost: number;
  client_discord_id: string;
  guild_id: string;
  vehicle_id: string;
  vehicle_type: string;
  vehicle_location: string;
  payment_method?: string;
  ingame_name: string;
  client_display_name?: string;
}

export interface VehiclePrice {
  id: number;
  guild_id: string;
  vehicle_type: string;
  price: number;
  updated_by: string;
  updated_at: string;
  is_active: boolean;
  price_multiplier: number;
  pvp_surcharge_percent: number;
}

export interface VehiclePriceCreate {
  guild_id: string;
  vehicle_type: string;
  price: number;
  updated_by: string;
  price_multiplier?: number;
  pvp_surcharge_percent?: number;
  is_active?: boolean;
}

export interface VehiclePriceUpdate {
  price: number;
  price_multiplier: number;
  pvp_surcharge_percent: number;
  is_active: boolean;
}

export interface MechanicStats {
  total_mechanics: number;
  active_mechanics: number;
  total_services: number;
  pending_services: number;
  completed_services: number;
  total_revenue: number;
  average_service_cost: number;
  most_popular_vehicle_type: string;
  busiest_mechanic?: string;
}

export interface MechanicPerformance {
  discord_id: string;
  ingame_name: string;
  total_services: number;
  completed_services: number;
  total_revenue: number;
  average_rating: number;
  completion_rate: number;
  average_response_time_hours: number;
}

export interface BulkPriceUpdate {
  vehicle_types: string[];
  price_adjustment_percent: number;
  updated_by: string;
}

// ================================
// API FUNCTIONS
// ================================

/**
 * Obtener configuración del sistema mecánico
 */
export const getMechanicConfig = async (guildId: string = '123456789'): Promise<MechanicConfig> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/config?guild_id=${guildId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch mechanic config: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Actualizar configuración del sistema mecánico
 */
export const updateMechanicConfig = async (
  guildId: string,
  config: MechanicConfigUpdate
): Promise<MechanicConfig> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/config?guild_id=${guildId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    throw new Error(`Failed to update mechanic config: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Obtener lista de mecánicos registrados
 */
export const getMechanics = async (guildId: string = '123456789'): Promise<RegisteredMechanic[]> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/mechanics?guild_id=${guildId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch mechanics: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Registrar un nuevo mecánico
 */
export const createMechanic = async (mechanic: MechanicCreate): Promise<RegisteredMechanic> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/mechanics`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(mechanic),
  });
  if (!response.ok) {
    throw new Error(`Failed to create mechanic: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Actualizar información de un mecánico
 */
export const updateMechanic = async (
  mechanicId: number,
  guildId: string,
  updates: MechanicUpdate
): Promise<RegisteredMechanic> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/mechanics/${mechanicId}?guild_id=${guildId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });
  if (!response.ok) {
    throw new Error(`Failed to update mechanic: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Eliminar un mecánico
 */
export const deleteMechanic = async (mechanicId: number, guildId: string = '123456789'): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/mechanics/${mechanicId}?guild_id=${guildId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete mechanic: ${response.statusText}`);
  }
};

/**
 * Obtener lista de servicios
 */
export const getServices = async (guildId: string = '123456789'): Promise<MechanicService[]> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/services?guild_id=${guildId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch services: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Crear un nuevo servicio
 */
export const createService = async (service: ServiceCreate): Promise<MechanicService> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/services`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(service),
  });
  if (!response.ok) {
    throw new Error(`Failed to create service: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Obtener precios de vehículos
 */
export const getVehiclePrices = async (guildId: string = '123456789'): Promise<VehiclePrice[]> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/vehicle-prices?guild_id=${guildId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch vehicle prices: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Crear precio para un tipo de vehículo
 */
export const createVehiclePrice = async (priceData: VehiclePriceCreate): Promise<VehiclePrice> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/vehicle-prices`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(priceData),
  });
  if (!response.ok) {
    throw new Error(`Failed to create vehicle price: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Actualizar precio de vehículo
 */
export const updateVehiclePrice = async (
  priceId: number,
  guildId: string,
  updates: VehiclePriceUpdate
): Promise<VehiclePrice> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/vehicle-prices/${priceId}?guild_id=${guildId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });
  if (!response.ok) {
    throw new Error(`Failed to update vehicle price: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Eliminar precio de vehículo
 */
export const deleteVehiclePrice = async (priceId: number, guildId: string = '123456789'): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/vehicle-prices/${priceId}?guild_id=${guildId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete vehicle price: ${response.statusText}`);
  }
};

/**
 * Obtener estadísticas del sistema mecánico
 */
export const getMechanicStats = async (guildId: string = '123456789'): Promise<MechanicStats> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/stats?guild_id=${guildId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch mechanic stats: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Obtener performance de mecánicos
 */
export const getMechanicPerformance = async (guildId: string = '123456789'): Promise<MechanicPerformance[]> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/performance?guild_id=${guildId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch mechanic performance: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Actualizar precios en masa
 */
export const bulkUpdatePrices = async (bulkUpdate: BulkPriceUpdate): Promise<{ updated_count: number }> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/mechanic/bulk-price-update`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(bulkUpdate),
  });
  if (!response.ok) {
    throw new Error(`Failed to bulk update prices: ${response.statusText}`);
  }
  return response.json();
};