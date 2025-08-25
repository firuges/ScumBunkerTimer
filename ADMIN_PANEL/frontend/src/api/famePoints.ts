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

  // Mock data for SQLite database simulation
  private mockRewards: FameReward[] = [
    {
      id: 1,
      guild_id: '123456789',
      fame_amount: 100,
      reward_description: '🥉 Bronce Reward - Rol bronce por 1 mes',
      reward_value: '{"role_id": "123456", "duration": 2628000}',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: 2,
      guild_id: '123456789',
      fame_amount: 250,
      reward_description: '🥈 Plata Reward - Rifle de asalto AK-74',
      reward_value: '{"item_name": "AK-74", "quantity": 1}',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: 3,
      guild_id: '123456789',
      fame_amount: 500,
      reward_description: '🥇 Oro Reward - $50,000 en efectivo',
      reward_value: '{"amount": 50000, "currency": "dollars"}',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: 4,
      guild_id: '123456789',
      fame_amount: 1000,
      reward_description: '💎 Platino Reward - Vehículo Hatchback',
      reward_value: '{"vehicle": "Hatchback_01", "condition": 100}',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: 5,
      guild_id: '123456789',
      fame_amount: 2500,
      reward_description: '🏆 Diamante Reward - Acceso a base premium',
      reward_value: '{"type": "base_access", "location": "premium_base"}',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: 6,
      guild_id: '123456789',
      fame_amount: 5000,
      reward_description: '👑 Leyenda Reward - Privilegios admin por 1 semana',
      reward_value: '{"type": "admin_privileges", "duration": 604800}',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  ];

  // Rewards CRUD
  async getRewards(guildId: string): Promise<FameReward[]> {
    try {
      // Try to get from API first
      return await apiClient.get<FameReward[]>(`${this.basePath}/rewards?guild_id=${guildId}`);
    } catch (error) {
      console.warn('API not available, using mock data from SQLite schema:', error);
      // Return mock data that simulates SQLite database content
      return this.mockRewards.filter(reward => reward.guild_id === guildId);
    }
  }

  async getReward(guildId: string, rewardId: number): Promise<FameReward> {
    return apiClient.get<FameReward>(`${this.basePath}/rewards/${rewardId}?guild_id=${guildId}`);
  }

  async createReward(guildId: string, reward: FameRewardCreate): Promise<FameReward> {
    try {
      const data = { ...reward, guild_id: guildId };
      return await apiClient.post<FameReward>(`${this.basePath}/rewards`, data);
    } catch (error) {
      console.warn('API not available, simulating create operation:', error);
      // Simulate creating new reward in SQLite
      const newReward: FameReward = {
        id: Math.max(...this.mockRewards.map(r => r.id || 0)) + 1,
        guild_id: guildId,
        fame_amount: reward.fame_amount,
        reward_description: reward.reward_description,
        reward_value: reward.reward_value,
        is_active: reward.is_active,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      this.mockRewards.push(newReward);
      return newReward;
    }
  }

  async updateReward(guildId: string, rewardId: number, reward: FameRewardUpdate): Promise<FameReward> {
    try {
      const data = { ...reward, guild_id: guildId };
      return await apiClient.put<FameReward>(`${this.basePath}/rewards/${rewardId}`, data);
    } catch (error) {
      console.warn('API not available, simulating update operation:', error);
      // Simulate updating reward in SQLite
      const index = this.mockRewards.findIndex(r => r.id === rewardId && r.guild_id === guildId);
      if (index !== -1) {
        this.mockRewards[index] = {
          ...this.mockRewards[index],
          ...reward,
          updated_at: new Date().toISOString()
        };
        return this.mockRewards[index];
      }
      throw new Error('Reward not found');
    }
  }

  async deleteReward(guildId: string, rewardId: number): Promise<void> {
    try {
      return await apiClient.delete(`${this.basePath}/rewards/${rewardId}?guild_id=${guildId}`);
    } catch (error) {
      console.warn('API not available, simulating delete operation:', error);
      // Simulate deleting from SQLite
      const index = this.mockRewards.findIndex(r => r.id === rewardId && r.guild_id === guildId);
      if (index !== -1) {
        this.mockRewards.splice(index, 1);
      }
    }
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