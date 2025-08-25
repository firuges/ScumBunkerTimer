import { apiClient } from './client';

// Server Management
export interface ServerInfo {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  max_bunkers: number;
  is_active: boolean;
  total_bunkers: number;
  active_bunkers: number;
}

export interface CreateServerRequest {
  guild_id: string;
  name: string;
  display_name: string;
  description?: string;
  max_bunkers: number;
}

// Sector Management
export interface SectorInfo {
  id: number;
  sector: string;
  name: string;
  coordinates?: string;
  description?: string;
  default_duration_hours: number;
  notification_enabled: boolean;
  is_active: boolean;
  total_registrations: number;
  active_registrations: number;
}

export interface CreateSectorRequest {
  guild_id: string;
  sector: string;
  name: string;
  coordinates?: string;
  description?: string;
  default_duration_hours: number;
}

// Bunker Registrations
export interface BunkerRegistration {
  id: number;
  sector: string;
  name: string;
  server_name: string;
  registered_time: string;
  expiry_time: string;
  registered_by: string;
  last_updated: string;
  status: 'active' | 'expired' | 'near_expiry' | 'unknown';
  time_remaining?: string;
  expired_minutes_ago?: number;
}

export interface RegisterBunkerRequest {
  guild_id: string;
  server_name: string;
  sector: string;
  hours: number;
  minutes?: number;
  registered_by: string;
}

// Statistics
export interface BunkersOverview {
  guild_id: string;
  stats: {
    total_servers: number;
    total_sectors: number;
    total_registrations: number;
    active_registrations: number;
    registrations_today: number;
    most_active_sector?: string;
  };
  health: 'healthy' | 'warning' | 'error';
}

export const bunkersAPI = {
  // Server Management
  async getServers(guildId: string = 'DEFAULT_GUILD'): Promise<ServerInfo[]> {
    return apiClient.get<ServerInfo[]>(`/bunkers/servers?guild_id=${guildId}`);
  },

  async createServer(serverData: CreateServerRequest): Promise<ServerInfo> {
    return apiClient.post<ServerInfo>('/bunkers/servers', serverData);
  },

  async deleteServer(serverId: number, guildId: string = 'DEFAULT_GUILD'): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/bunkers/servers/${serverId}?guild_id=${guildId}`);
  },

  // Sector Management
  async getSectors(guildId: string = 'DEFAULT_GUILD'): Promise<SectorInfo[]> {
    return apiClient.get<SectorInfo[]>(`/bunkers/sectors?guild_id=${guildId}`);
  },

  async createSector(sectorData: CreateSectorRequest): Promise<SectorInfo> {
    return apiClient.post<SectorInfo>('/bunkers/sectors', sectorData);
  },

  async deleteSector(sectorId: number, guildId: string = 'DEFAULT_GUILD'): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/bunkers/sectors/${sectorId}?guild_id=${guildId}`);
  },

  // Bunker Registrations
  async getRegistrations(
    guildId: string = 'DEFAULT_GUILD',
    serverName?: string,
    limit: number = 50
  ): Promise<BunkerRegistration[]> {
    let url = `/bunkers/registrations?guild_id=${guildId}&limit=${limit}`;
    if (serverName) {
      url += `&server_name=${serverName}`;
    }
    return apiClient.get<BunkerRegistration[]>(url);
  },

  async registerBunker(registration: RegisterBunkerRequest): Promise<{ 
    message: string; 
    sector: string; 
    server: string; 
    expiry_time: string; 
    duration: string 
  }> {
    return apiClient.post<{ 
      message: string; 
      sector: string; 
      server: string; 
      expiry_time: string; 
      duration: string 
    }>('/bunkers/registrations/manual', registration);
  },

  async cancelRegistration(bunkerId: number, guildId: string = 'DEFAULT_GUILD'): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/bunkers/registrations/${bunkerId}?guild_id=${guildId}`);
  },

  // Statistics
  async getOverview(guildId: string = 'DEFAULT_GUILD'): Promise<BunkersOverview> {
    return apiClient.get<BunkersOverview>(`/bunkers/stats/overview?guild_id=${guildId}`);
  }
};