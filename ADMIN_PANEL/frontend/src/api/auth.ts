/**
 * Authentication API functions
 */

import { apiClient } from './client';

export interface DiscordUser {
  id: string;
  username: string;
  discriminator: string;
  avatar?: string;
  email?: string;
}

export interface UserProfile {
  id: string;
  discord_id: string;
  username: string;
  discriminator: string;
  avatar_url?: string;
  role: 'super_admin' | 'guild_admin' | 'moderator' | 'viewer';
  status: 'active' | 'suspended' | 'banned';
  guilds: string[];
  permissions: string[];
  created_at: string;
  last_login?: string;
}

export interface LoginRequest {
  code: string;
  state?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface UserPermissions {
  user: string;
  role: string;
  permissions: Record<string, boolean>;
  modules: string[];
}

export interface DiscordOAuthUrl {
  url: string;
}

export class AuthAPI {
  /**
   * Get Discord OAuth2 authorization URL
   */
  static async getDiscordOAuthUrl(): Promise<DiscordOAuthUrl> {
    return apiClient.get<DiscordOAuthUrl>('/auth/discord-url');
  }

  /**
   * Login with Discord OAuth2 code
   */
  static async login(loginData: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/login', loginData);
    
    // Store token in client
    apiClient.setToken(response.access_token);
    
    return response;
  }

  /**
   * Logout current user
   */
  static async logout(token: string, logoutAllDevices = false): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/auth/logout', {
      token,
      logout_all_devices: logoutAllDevices,
    });
    
    // Clear token from client
    apiClient.clearToken();
    
    return response;
  }

  /**
   * Get current user profile
   */
  static async getCurrentUser(): Promise<UserProfile> {
    return apiClient.get<UserProfile>('/auth/me');
  }

  /**
   * Get current user permissions
   */
  static async getUserPermissions(): Promise<UserPermissions> {
    return apiClient.get<UserPermissions>('/auth/permissions');
  }

  /**
   * Get all admin users (super_admin only)
   */
  static async getAllUsers(): Promise<{ users: UserProfile[] }> {
    return apiClient.get<{ users: UserProfile[] }>('/auth/users');
  }

  /**
   * Update user role and permissions (super_admin only)
   */
  static async updateUser(
    userId: string,
    updates: {
      role?: UserProfile['role'];
      status?: UserProfile['status'];
      permissions?: string[];
    }
  ): Promise<{ message: string }> {
    return apiClient.put<{ message: string }>(`/auth/users/${userId}`, updates);
  }

  /**
   * Check if user has specific permission
   */
  static hasPermission(userPermissions: UserPermissions, permission: string): boolean {
    return userPermissions.permissions[permission] === true;
  }

  /**
   * Check if user can access module
   */
  static canAccessModule(userPermissions: UserPermissions, module: string): boolean {
    return userPermissions.modules.includes(module);
  }

  /**
   * Get user's accessible guilds
   */
  static getAccessibleGuilds(user: UserProfile): string[] {
    return user.guilds || [];
  }

  /**
   * Check if user has access to specific guild
   */
  static hasGuildAccess(user: UserProfile, guildId: string): boolean {
    return user.role === 'super_admin' || user.guilds.includes(guildId);
  }
}