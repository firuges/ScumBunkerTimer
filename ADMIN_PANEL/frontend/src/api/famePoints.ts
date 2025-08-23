import { apiClient } from './client';

export interface FameReward {
  id?: number;
  guild_id: string;
  fame_amount: number;
  reward_description: string;
  reward_value: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface FameRewardCreate {
  fame_amount: number;
  reward_description: string;
  reward_value: string;
  is_active: boolean;
}

export interface FameRewardUpdate {
  fame_amount?: number;
  reward_description?: string;
  reward_value?: string;
  is_active?: boolean;
}

export interface FameClaim {
  id: number;
  user_discord_id: string;
  user_display_name: string;
  fame_amount: number;
  reward_description: string;
  reward_value: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}

export interface FameStats {
  total_rewards: number;
  active_rewards: number;
  total_claims: number;
  pending_claims: number;
  total_fame_distributed: number;
}

class FamePointsAPI {
  private basePath = '/fame';

  // Rewards CRUD
  async getRewards(guildId: string): Promise<FameReward[]> {
    return apiClient.get<FameReward[]>(`${this.basePath}/${guildId}/rewards`);
  }

  async getReward(guildId: string, rewardId: number): Promise<FameReward> {
    return apiClient.get<FameReward>(`${this.basePath}/${guildId}/rewards/${rewardId}`);
  }

  async createReward(guildId: string, reward: FameRewardCreate): Promise<FameReward> {
    return apiClient.post<FameReward>(`${this.basePath}/${guildId}/rewards`, reward);
  }

  async updateReward(guildId: string, rewardId: number, reward: FameRewardUpdate): Promise<FameReward> {
    return apiClient.put<FameReward>(`${this.basePath}/${guildId}/rewards/${rewardId}`, reward);
  }

  async deleteReward(guildId: string, rewardId: number): Promise<void> {
    return apiClient.delete(`${this.basePath}/${guildId}/rewards/${rewardId}`);
  }

  // Claims management
  async getClaims(guildId: string, status?: string): Promise<FameClaim[]> {
    const params = status ? { status } : {};
    return apiClient.get<FameClaim[]>(`${this.basePath}/${guildId}/claims`, { params });
  }

  async approveClaim(guildId: string, claimId: number): Promise<FameClaim> {
    return apiClient.post<FameClaim>(`${this.basePath}/${guildId}/claims/${claimId}/approve`);
  }

  async rejectClaim(guildId: string, claimId: number, reason?: string): Promise<FameClaim> {
    return apiClient.post<FameClaim>(`${this.basePath}/${guildId}/claims/${claimId}/reject`, { reason });
  }

  // Statistics
  async getStats(guildId: string): Promise<FameStats> {
    return apiClient.get<FameStats>(`${this.basePath}/${guildId}/stats`);
  }

  // Guild configuration
  async getGuildConfig(guildId: string): Promise<any> {
    return apiClient.get(`${this.basePath}/${guildId}/config`);
  }

  async updateGuildConfig(guildId: string, config: any): Promise<any> {
    return apiClient.put(`${this.basePath}/${guildId}/config`, config);
  }

  // Sync with bot
  async syncWithBot(guildId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.post(`${this.basePath}/${guildId}/sync`);
  }
}

export const famePointsAPI = new FamePointsAPI();
export default famePointsAPI;