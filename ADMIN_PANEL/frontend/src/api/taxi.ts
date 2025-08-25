const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Taxi Configuration Types
export interface TaxiConfig {
  id: number;
  guild_id: string;
  taxi_channel_id?: string;
  base_fare: number;
  per_km_rate: number;
  commission_percent: number;
  max_distance_km: number;
  min_fare: number;
  waiting_time_rate: number;
  night_multiplier: number;
  peak_hours_multiplier: number;
  peak_hours_start: string;
  peak_hours_end: string;
  auto_accept_distance: number;
  driver_minimum_level: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  updated_by: number;
}

export interface TaxiConfigUpdate {
  taxi_channel_id?: string;
  base_fare: number;
  per_km_rate: number;
  commission_percent: number;
  max_distance_km: number;
  min_fare: number;
  waiting_time_rate: number;
  night_multiplier: number;
  peak_hours_multiplier: number;
  peak_hours_start: string;
  peak_hours_end: string;
  auto_accept_distance: number;
  driver_minimum_level: number;
  is_active: boolean;
}

// Vehicle Types
export interface Vehicle {
  id: number;
  guild_id: string;
  vehicle_name: string;
  display_name: string;
  description?: string;
  base_multiplier: number;
  comfort_multiplier: number;
  speed_multiplier: number;
  capacity_passengers: number;
  fuel_consumption: number;
  maintenance_cost: number;
  unlock_level: number;
  purchase_cost: number;
  emoji: string;
  is_active: boolean;
  is_premium: boolean;
  created_at: string;
}

export interface VehicleCreate {
  guild_id: string;
  vehicle_name: string;
  display_name: string;
  description?: string;
  base_multiplier: number;
  comfort_multiplier: number;
  speed_multiplier: number;
  capacity_passengers: number;
  fuel_consumption: number;
  maintenance_cost: number;
  unlock_level: number;
  purchase_cost: number;
  emoji: string;
  is_active: boolean;
  is_premium: boolean;
}

// Zone Types
export interface TaxiZone {
  id: number;
  guild_id: string;
  zone_name: string;
  display_name: string;
  description?: string;
  zone_type: string;
  danger_multiplier: number;
  min_driver_level: number;
  allowed_vehicles: string;
  restricted_hours?: string;
  coordinate_bounds?: string;
  warning_message?: string;
  requires_confirmation: boolean;
  is_active: boolean;
  created_at: string;
}

export interface TaxiZoneCreate {
  guild_id: string;
  zone_name: string;
  display_name: string;
  description?: string;
  zone_type: string;
  danger_multiplier: number;
  min_driver_level: number;
  allowed_vehicles: string;
  restricted_hours?: string;
  coordinate_bounds?: string;
  warning_message?: string;
  requires_confirmation: boolean;
  is_active: boolean;
}

// Taxi Stop Types
export interface TaxiStop {
  id: number;
  guild_id: string;
  stop_name: string;
  display_name: string;
  description?: string;
  coordinate_x: number;
  coordinate_y: number;
  coordinate_z: number;
  zone_id?: number;
  is_pickup_point: boolean;
  is_dropoff_point: boolean;
  popularity_bonus: number;
  waiting_area_size: number;
  landmark_type: string;
  emoji: string;
  is_active: boolean;
  created_at: string;
}

export interface TaxiStopCreate {
  guild_id: string;
  stop_name: string;
  display_name: string;
  description?: string;
  coordinate_x: number;
  coordinate_y: number;
  coordinate_z: number;
  zone_id?: number;
  is_pickup_point: boolean;
  is_dropoff_point: boolean;
  popularity_bonus: number;
  waiting_area_size: number;
  landmark_type: string;
  emoji: string;
  is_active: boolean;
}

// Driver Level Types
export interface DriverLevel {
  id: number;
  guild_id: string;
  level: number;
  level_name: string;
  description?: string;
  required_trips: number;
  required_distance: number;
  earnings_multiplier: number;
  tip_multiplier: number;
  unlock_vehicles: string;
  unlock_zones: string;
  special_perks: string;
  badge_emoji: string;
  is_active: boolean;
  created_at: string;
}

// Pricing Types
export interface PricingRule {
  id: number;
  guild_id: string;
  pricing_name: string;
  display_name: string;
  description?: string;
  pricing_type: string;
  multiplier_value: number;
  discount_amount: number;
  min_distance: number;
  max_distance: number;
  applicable_zones: string;
  applicable_vehicles: string;
  start_time?: string;
  end_time?: string;
  days_of_week: string;
  start_date?: string;
  end_date?: string;
  priority: number;
  is_active: boolean;
  created_at: string;
}

// Fare Calculator Types
export interface FareCalculationRequest {
  origin_x: number;
  origin_y: number;
  destination_x: number;
  destination_y: number;
  vehicle_type: string;
  zone_type?: string;
  driver_level: number;
  is_night_time: boolean;
  is_peak_hours: boolean;
}

export interface FareCalculationResponse {
  base_fare: number;
  distance_km: number;
  distance_fare: number;
  vehicle_multiplier: number;
  zone_multiplier: number;
  time_multiplier: number;
  driver_bonus: number;
  commission: number;
  total_fare: number;
  driver_earnings: number;
  breakdown: {
    base_fare: number;
    distance_fare: number;
    vehicle_bonus: number;
    zone_bonus: number;
    time_bonus: number;
    driver_bonus: number;
    commission_rate: number;
  };
}

// API Client
export const taxiAPI = {
  // Taxi Configuration
  async getConfig(guildId: string = '123456789'): Promise<TaxiConfig> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/taxi/config?guild_id=${guildId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch taxi configuration');
    }
    
    return response.json();
  },

  async updateConfig(guildId: string = '123456789', config: TaxiConfigUpdate): Promise<TaxiConfig> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/taxi/config?guild_id=${guildId}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to update taxi configuration');
    }
    
    return response.json();
  },

  // Vehicles
  async getVehicles(guildId: string = '123456789'): Promise<Vehicle[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/taxi/vehicles?guild_id=${guildId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch vehicles');
    }
    
    return response.json();
  },

  async createVehicle(vehicle: any, guildId: string = '123456789'): Promise<Vehicle> {
    const vehicleData = { ...vehicle, guild_id: guildId };
    const response = await fetch(`${API_BASE_URL}/api/v1/taxi/vehicles`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(vehicleData),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create vehicle');
    }
    
    return response.json();
  },

  async updateVehicle(vehicleId: number, vehicle: any, guildId: string = '123456789'): Promise<Vehicle> {
    const vehicleData = { ...vehicle, guild_id: guildId };
    const response = await fetch(`${API_BASE_URL}/api/v1/taxi/vehicles/${vehicleId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(vehicleData),
    });
    
    if (!response.ok) {
      throw new Error('Failed to update vehicle');
    }
    
    return response.json();
  },

  async deleteVehicle(vehicleId: number, guildId: string = '123456789'): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/taxi/vehicles/${vehicleId}?guild_id=${guildId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete vehicle');
    }
  },

  // Zones
  async getZones(guildId: string = '123456789'): Promise<TaxiZone[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/taxi/zones?guild_id=${guildId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch zones');
    }
    
    return response.json();
  },

  async createZone(zone: TaxiZoneCreate): Promise<TaxiZone> {
    const response = await fetch(`${API_BASE_URL}/api/v1/taxi/zones`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(zone),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create zone');
    }
    
    return response.json();
  },

  async updateZone(zoneId: number, zone: any, guildId: string = '123456789'): Promise<TaxiZone> {
    const zoneData = { ...zone, guild_id: guildId };
    const response = await fetch(`${API_BASE_URL}/api/v1/taxi/zones/${zoneId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(zoneData),
    });
    
    if (!response.ok) {
      throw new Error('Failed to update zone');
    }
    
    return response.json();
  },

  async deleteZone(zoneId: number, guildId: string = '123456789'): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/taxi/zones/${zoneId}?guild_id=${guildId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete zone');
    }
  },

  // Taxi Stops
  async getStops(guildId: string = '123456789'): Promise<TaxiStop[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/taxi/stops?guild_id=${guildId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch taxi stops');
    }
    
    return response.json();
  },

  async createStop(stop: TaxiStopCreate): Promise<TaxiStop> {
    const response = await fetch(`${API_BASE_URL}/api/v1/taxi/stops`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(stop),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create taxi stop');
    }
    
    return response.json();
  },

  async updateStop(stopId: number, stop: any, guildId: string = '123456789'): Promise<TaxiStop> {
    const stopData = { ...stop, guild_id: guildId };
    const response = await fetch(`${API_BASE_URL}/api/v1/taxi/stops/${stopId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(stopData),
    });
    
    if (!response.ok) {
      throw new Error('Failed to update taxi stop');
    }
    
    return response.json();
  },

  async deleteStop(stopId: number, guildId: string = '123456789'): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/taxi/stops/${stopId}?guild_id=${guildId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete taxi stop');
    }
  },

  // Driver Levels
  async getDriverLevels(guildId: string = '123456789'): Promise<DriverLevel[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/taxi/driver-levels?guild_id=${guildId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch driver levels');
    }
    
    return response.json();
  },

  // Pricing Rules
  async getPricingRules(guildId: string = '123456789'): Promise<PricingRule[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/taxi/pricing?guild_id=${guildId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch pricing rules');
    }
    
    return response.json();
  },

  // Fare Calculator
  async calculateFare(request: FareCalculationRequest, guildId: string = '123456789'): Promise<FareCalculationResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/taxi/calculate-fare?guild_id=${guildId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to calculate fare');
    }
    
    return response.json();
  },
};