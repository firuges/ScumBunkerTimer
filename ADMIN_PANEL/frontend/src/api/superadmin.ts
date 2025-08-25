/**
 * Super Admin API Client - Gestión global cross-server
 * Para el dueño del bot con control total del ecosystem
 */

import { apiClient } from './client';

// Types
export interface GlobalAnalytics {
  total_servers: number;
  active_servers: number;
  premium_servers: number;
  vip_servers: number;
  total_users: number;
  daily_active_users: number;
  monthly_revenue: number;
  top_features: Array<{
    feature: string;
    usage: number;
    growth: string;
  }>;
  growth_metrics: {
    new_servers_today: number;
    new_servers_week: number;
    new_servers_month: number;
    churned_servers_month: number;
  };
  system_health: {
    overall_uptime: number;
    api_response_time: number;
    database_performance: number;
    error_rate: number;
  };
}

export interface DiscordServerInfo {
  guild_id: string;
  guild_name: string;
  owner_id: string;
  owner_username: string;
  member_count: number;
  created_at: string;
  subscription_plan: 'free' | 'premium' | 'vip';
  status: 'active' | 'inactive' | 'suspended' | 'trial';
  last_activity?: string;
  features_enabled: string[];
  monthly_usage: {
    commands: number;
    api_calls: number;
    active_users: number;
  };
}

export interface ServerUsageStats {
  guild_id: string;
  guild_name: string;
  commands_used_today: number;
  commands_used_month: number;
  active_users_today: number;
  active_users_month: number;
  most_used_features: string[];
  revenue_generated: number;
  last_activity: string;
}

export interface SystemHealthCheck {
  service_name: string;
  status: 'healthy' | 'warning' | 'error';
  response_time: number;
  uptime_percentage: number;
  last_check: string;
  error_count: number;
  details?: Record<string, any>;
}

export interface AdminAction {
  id: number;
  admin_id: string;
  admin_username: string;
  action_type: string;
  target_guild_id?: string;
  details: Record<string, any>;
  timestamp: string;
  ip_address?: string;
}

export interface GlobalDashboard {
  analytics: GlobalAnalytics;
  recent_actions: AdminAction[];
  system_health: SystemHealthCheck[];
  top_servers: ServerUsageStats[];
  alerts: string[];
}

export interface ServerManagement {
  servers: DiscordServerInfo[];
  total_count: number;
  filter_applied?: string;
  subscription_summary: {
    free: number;
    premium: number;
    vip: number;
  };
}

export interface SubscriptionHistory {
  id: number;
  guild_id: string;
  plan: 'free' | 'premium' | 'vip';
  start_date: string;
  end_date?: string;
  status: string;
  upgraded_by: string;
  reason?: string;
}

export interface SubscriptionManagement {
  active_subscriptions: SubscriptionHistory[];
  revenue_summary: {
    monthly_recurring: number;
    total_this_month: number;
    total_last_month: number;
    annual_projection: number;
  };
  upcoming_renewals: DiscordServerInfo[];
  expired_subscriptions: DiscordServerInfo[];
}

export interface SubscriptionUpdate {
  guild_id: string;
  new_plan: 'free' | 'premium' | 'vip';
  duration_months: number;
  reason?: string;
}

export interface ServerActionBulk {
  guild_ids: string[];
  action: string;
  reason: string;
  new_plan?: 'free' | 'premium' | 'vip';
}

// API Client
const OWNER_ID = 'OWNER_ID_PLACEHOLDER'; // In production, get from auth

export const superAdminAPI = {
  // Global Dashboard
  async getDashboard(): Promise<GlobalDashboard> {
    return apiClient.get<GlobalDashboard>(`/superadmin/dashboard?owner_id=${OWNER_ID}`);
  },

  // Server Management
  async getAllServers(statusFilter?: string, planFilter?: string, limit: number = 50): Promise<ServerManagement> {
    let url = `/superadmin/servers?owner_id=${OWNER_ID}&limit=${limit}`;
    if (statusFilter) url += `&status_filter=${statusFilter}`;
    if (planFilter) url += `&plan_filter=${planFilter}`;
    
    return apiClient.get<ServerManagement>(url);
  },

  // Subscription Management  
  async updateServerSubscription(guildId: string, update: SubscriptionUpdate): Promise<any> {
    return apiClient.put<any>(
      `/superadmin/servers/${guildId}/subscription?owner_id=${OWNER_ID}`,
      update
    );
  },

  async getSubscriptionManagement(): Promise<SubscriptionManagement> {
    return apiClient.get<SubscriptionManagement>(`/superadmin/subscriptions?owner_id=${OWNER_ID}`);
  },

  // Bulk Operations
  async bulkServerAction(actionRequest: ServerActionBulk): Promise<any> {
    return apiClient.post<any>(
      `/superadmin/servers/bulk-action?owner_id=${OWNER_ID}`,
      actionRequest
    );
  },

  // Health Check
  async healthCheck(): Promise<any> {
    return apiClient.get<any>('/superadmin/health');
  }
};

export default superAdminAPI;