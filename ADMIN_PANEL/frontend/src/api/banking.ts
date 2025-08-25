const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface BankingConfig {
  id: number;
  guild_id: string;
  bank_channel_id?: string;
  welcome_bonus: number;
  daily_bonus: number;
  min_balance: number;
  max_balance: number;
  transfer_fee_percent: number;
  min_transfer_amount: number;
  max_transfer_amount: number;
  max_daily_transfers: number;
  overdraft_enabled: boolean;
  overdraft_limit: number;
  interest_rate: number;
  bank_hours_start: string;
  bank_hours_end: string;
  weekend_enabled: boolean;
  created_at: string;
  updated_at: string;
  updated_by: number;
}

export interface BankingConfigCreate {
  guild_id: string;
  bank_channel_id?: string;
  welcome_bonus: number;
  daily_bonus: number;
  min_balance: number;
  max_balance: number;
  transfer_fee_percent: number;
  min_transfer_amount: number;
  max_transfer_amount: number;
  max_daily_transfers: number;
  overdraft_enabled: boolean;
  overdraft_limit: number;
  interest_rate: number;
  bank_hours_start: string;
  bank_hours_end: string;
  weekend_enabled: boolean;
}

export interface BankingConfigUpdate {
  bank_channel_id?: string;
  welcome_bonus: number;
  daily_bonus: number;
  min_balance: number;
  max_balance: number;
  transfer_fee_percent: number;
  min_transfer_amount: number;
  max_transfer_amount: number;
  max_daily_transfers: number;
  overdraft_enabled: boolean;
  overdraft_limit: number;
  interest_rate: number;
  bank_hours_start: string;
  bank_hours_end: string;
  weekend_enabled: boolean;
}

export interface AccountType {
  id: number;
  guild_id: string;
  account_type_name: string;
  display_name: string;
  description?: string;
  min_balance: number;
  max_balance: number;
  daily_limit: number;
  transfer_fee_percent: number;
  monthly_fee: number;
  interest_rate: number;
  overdraft_limit: number;
  required_role?: string;
  is_active: boolean;
  created_at: string;
}

export interface AccountTypeCreate {
  guild_id: string;
  account_type_name: string;
  display_name: string;
  description?: string;
  min_balance: number;
  max_balance: number;
  daily_limit: number;
  transfer_fee_percent: number;
  monthly_fee: number;
  interest_rate: number;
  overdraft_limit: number;
  required_role?: string;
  is_active: boolean;
}

export interface BankingFee {
  id: number;
  guild_id: string;
  fee_type: 'transfer' | 'withdrawal' | 'deposit' | 'maintenance';
  fee_name: string;
  fee_method: 'percentage' | 'fixed' | 'tiered';
  fee_value: number;
  min_amount: number;
  max_amount?: number;
  applies_to: string;
  description?: string;
  is_active: boolean;
  created_at: string;
}

export interface BankingChannel {
  id: number;
  guild_id: string;
  channel_type: 'main' | 'logs' | 'announcements' | 'support';
  channel_id: string;
  channel_name?: string;
  auto_delete_messages: boolean;
  delete_after_minutes: number;
  embed_color: string;
  ping_role?: string;
  is_active: boolean;
  created_at: string;
}

export interface BankingChannelCreate {
  guild_id: string;
  channel_type: 'main' | 'logs' | 'announcements' | 'support';
  channel_id: string;
  channel_name?: string;
  auto_delete_messages: boolean;
  delete_after_minutes: number;
  embed_color: string;
  ping_role?: string;
  is_active: boolean;
}

export const bankingAPI = {
  // Banking Configuration
  async getConfig(guildId: string = '123456789'): Promise<BankingConfig> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/banking/config?guild_id=${guildId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch banking configuration');
    }
    
    return response.json();
  },

  async createConfig(config: BankingConfigCreate): Promise<BankingConfig> {
    const response = await fetch(`${API_BASE_URL}/api/v1/banking/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create banking configuration');
    }
    
    return response.json();
  },

  async updateConfig(config: BankingConfigUpdate, guildId: string = '123456789'): Promise<BankingConfig> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/banking/config?guild_id=${guildId}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to update banking configuration');
    }
    
    return response.json();
  },

  // Account Types
  async getAccountTypes(guildId: string = '123456789'): Promise<AccountType[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/banking/account-types?guild_id=${guildId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch account types');
    }
    
    return response.json();
  },

  async createAccountType(accountType: AccountTypeCreate): Promise<AccountType> {
    const response = await fetch(`${API_BASE_URL}/api/v1/banking/account-types`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(accountType),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create account type');
    }
    
    return response.json();
  },

  // Banking Fees
  async getFees(guildId: string = '123456789'): Promise<BankingFee[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/banking/fees?guild_id=${guildId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch banking fees');
    }
    
    return response.json();
  },

  // Banking Channels
  async getChannels(guildId: string = '123456789'): Promise<BankingChannel[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/banking/channels?guild_id=${guildId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch banking channels');
    }
    
    return response.json();
  },

  async createChannel(channel: BankingChannelCreate): Promise<BankingChannel> {
    const response = await fetch(`${API_BASE_URL}/api/v1/banking/channels`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(channel),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create banking channel');
    }
    
    return response.json();
  },
};