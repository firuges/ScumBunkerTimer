/**
 * Analytics API Client - TypeScript
 * Cliente para el módulo Analytics del Admin Panel
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Types
export interface FamePointsMetrics {
  total_rewards: number;
  total_points_distributed: number;
  most_popular_reward?: string;
  average_points_per_reward: number;
  active_rewards: number;
}

export interface BankingMetrics {
  total_accounts: number;
  total_balance: number;
  account_types: Record<string, number>;
  total_fees_collected: number;
  average_balance: number;
}

export interface TaxiMetrics {
  total_vehicles: number;
  active_zones: number;
  total_stops: number;
  total_rides_completed: number;
  total_revenue: number;
  average_fare: number;
  most_popular_vehicle?: string;
}

export interface MechanicMetrics {
  total_mechanics: number;
  active_mechanics: number;
  total_services: number;
  completed_services: number;
  pending_services: number;
  total_revenue: number;
  average_service_cost: number;
}

export interface ActivityLog {
  timestamp: string;
  system: string;
  action: string;
  details: string;
  user_id?: string;
}

export interface AnalyticsDashboard {
  guild_id: string;
  generated_at: string;
  total_systems_active: number;
  total_database_records: number;
  fame_metrics: FamePointsMetrics;
  banking_metrics: BankingMetrics;
  taxi_metrics: TaxiMetrics;
  mechanic_metrics: MechanicMetrics;
  recent_activity: ActivityLog[];
  system_activity_comparison: Record<string, number>;
  growth_trends: Record<string, Record<string, number>>;
}

export interface SystemHealth {
  system_name: string;
  status: string;
  last_check: string;
  response_time: number;
  error_count: number;
  uptime_percentage: number;
}

export interface PerformanceMetrics {
  api_response_times: Record<string, number>;
  database_query_times: Record<string, number>;
  error_rates: Record<string, number>;
  active_sessions: number;
  peak_usage_hours: number[];
}

export interface AnalyticsReport {
  dashboard: AnalyticsDashboard;
  system_health: SystemHealth[];
  performance: PerformanceMetrics;
  recommendations: string[];
}

// API Functions
export const getAnalyticsDashboard = async (guildId: string = '123456789'): Promise<AnalyticsDashboard> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/analytics/dashboard?guild_id=${guildId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch dashboard: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching analytics dashboard:', error);
    throw error;
  }
};

export const getSystemHealth = async (guildId: string = '123456789'): Promise<SystemHealth[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/analytics/system-health?guild_id=${guildId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch system health: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching system health:', error);
    throw error;
  }
};

export const getPerformanceMetrics = async (guildId: string = '123456789'): Promise<PerformanceMetrics> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/analytics/performance?guild_id=${guildId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch performance metrics: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching performance metrics:', error);
    throw error;
  }
};

export const getAnalyticsReport = async (guildId: string = '123456789'): Promise<AnalyticsReport> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/analytics/report?guild_id=${guildId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch analytics report: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching analytics report:', error);
    throw error;
  }
};

export const getRecentActivity = async (
  guildId: string = '123456789',
  hours: number = 24
): Promise<ActivityLog[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/analytics/activity?guild_id=${guildId}&hours=${hours}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch recent activity: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching recent activity:', error);
    throw error;
  }
};