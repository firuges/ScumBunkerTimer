import React, { useState, useEffect } from 'react';
import { CogIcon, BanknotesIcon, ClockIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { bankingAPI, BankingConfig, BankingConfigUpdate } from '../api/banking';

export const BankingConfigPage: React.FC = () => {
  const [config, setConfig] = useState<BankingConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Mock guild ID - in real app this would come from auth context
  const guildId = '123456789';

  // Load config from API
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await bankingAPI.getConfig(guildId);
      setConfig(data);
    } catch (err: any) {
      console.error('Error loading banking config:', err);
      setError('Failed to load banking configuration. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const updateData: BankingConfigUpdate = {
        bank_channel_id: config.bank_channel_id,
        welcome_bonus: config.welcome_bonus,
        daily_bonus: config.daily_bonus,
        min_balance: config.min_balance,
        max_balance: config.max_balance,
        transfer_fee_percent: config.transfer_fee_percent,
        min_transfer_amount: config.min_transfer_amount,
        max_transfer_amount: config.max_transfer_amount,
        max_daily_transfers: config.max_daily_transfers,
        overdraft_enabled: config.overdraft_enabled,
        overdraft_limit: config.overdraft_limit,
        interest_rate: config.interest_rate,
        bank_hours_start: config.bank_hours_start,
        bank_hours_end: config.bank_hours_end,
        weekend_enabled: config.weekend_enabled,
      };

      const updatedConfig = await bankingAPI.updateConfig(updateData, guildId);
      setConfig(updatedConfig);
      setSuccess('Banking configuration updated successfully!');
    } catch (err: any) {
      console.error('Error updating config:', err);
      setError('Failed to update banking configuration. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof BankingConfig, value: any) => {
    if (!config) return;
    setConfig({ ...config, [field]: value });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (!config) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load banking configuration.</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="py-6">
        {/* Header */}
        <div className="md:flex md:items-center md:justify-between mb-8">
          <div className="flex-1 min-w-0">
            <h1 className="text-3xl font-bold text-gray-900">Banking Configuration</h1>
            <p className="mt-2 text-sm text-gray-600">
              Configure the banking system settings for your Discord server
            </p>
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
            <span className="block sm:inline">{error}</span>
            <button
              className="absolute top-0 bottom-0 right-0 px-4 py-3"
              onClick={() => setError(null)}
            >
              ×
            </button>
          </div>
        )}

        {success && (
          <div className="mb-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative">
            <span className="block sm:inline">{success}</span>
            <button
              className="absolute top-0 bottom-0 right-0 px-4 py-3"
              onClick={() => setSuccess(null)}
            >
              ×
            </button>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-8">
          {/* General Settings */}
          <div className="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
            <div className="md:grid md:grid-cols-3 md:gap-6">
              <div className="md:col-span-1">
                <div className="flex items-center">
                  <CogIcon className="h-6 w-6 text-gray-400 mr-2" />
                  <h3 className="text-lg font-medium leading-6 text-gray-900">General Settings</h3>
                </div>
                <p className="mt-1 text-sm text-gray-600">
                  Basic configuration for the banking system
                </p>
              </div>
              <div className="mt-5 md:mt-0 md:col-span-2">
                <div className="grid grid-cols-6 gap-6">
                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="bank_channel_id" className="block text-sm font-medium text-gray-700">
                      Bank Channel ID
                    </label>
                    <input
                      type="text"
                      id="bank_channel_id"
                      value={config.bank_channel_id || ''}
                      onChange={(e) => handleInputChange('bank_channel_id', e.target.value)}
                      className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                      placeholder="123456789012345678"
                    />
                  </div>

                  <div className="col-span-6 sm:col-span-3">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={config.weekend_enabled}
                        onChange={(e) => handleInputChange('weekend_enabled', e.target.checked)}
                        className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                      />
                      <label className="ml-2 text-sm text-gray-700">
                        Enable Weekend Banking
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Money Settings */}
          <div className="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
            <div className="md:grid md:grid-cols-3 md:gap-6">
              <div className="md:col-span-1">
                <div className="flex items-center">
                  <BanknotesIcon className="h-6 w-6 text-gray-400 mr-2" />
                  <h3 className="text-lg font-medium leading-6 text-gray-900">Money Settings</h3>
                </div>
                <p className="mt-1 text-sm text-gray-600">
                  Configure bonuses, limits, and fees
                </p>
              </div>
              <div className="mt-5 md:mt-0 md:col-span-2">
                <div className="grid grid-cols-6 gap-6">
                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="welcome_bonus" className="block text-sm font-medium text-gray-700">
                      Welcome Bonus
                    </label>
                    <input
                      type="number"
                      id="welcome_bonus"
                      value={config.welcome_bonus}
                      onChange={(e) => handleInputChange('welcome_bonus', parseInt(e.target.value) || 0)}
                      className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                      min="0"
                    />
                  </div>

                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="daily_bonus" className="block text-sm font-medium text-gray-700">
                      Daily Bonus
                    </label>
                    <input
                      type="number"
                      id="daily_bonus"
                      value={config.daily_bonus}
                      onChange={(e) => handleInputChange('daily_bonus', parseInt(e.target.value) || 0)}
                      className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                      min="0"
                    />
                  </div>

                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="transfer_fee_percent" className="block text-sm font-medium text-gray-700">
                      Transfer Fee (%)
                    </label>
                    <input
                      type="number"
                      id="transfer_fee_percent"
                      value={config.transfer_fee_percent}
                      onChange={(e) => handleInputChange('transfer_fee_percent', parseFloat(e.target.value) || 0)}
                      className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                      min="0"
                      max="100"
                      step="0.1"
                    />
                  </div>

                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="interest_rate" className="block text-sm font-medium text-gray-700">
                      Interest Rate (%)
                    </label>
                    <input
                      type="number"
                      id="interest_rate"
                      value={config.interest_rate}
                      onChange={(e) => handleInputChange('interest_rate', parseFloat(e.target.value) || 0)}
                      className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                      min="0"
                      max="100"
                      step="0.01"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Banking Hours */}
          <div className="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
            <div className="md:grid md:grid-cols-3 md:gap-6">
              <div className="md:col-span-1">
                <div className="flex items-center">
                  <ClockIcon className="h-6 w-6 text-gray-400 mr-2" />
                  <h3 className="text-lg font-medium leading-6 text-gray-900">Banking Hours</h3>
                </div>
                <p className="mt-1 text-sm text-gray-600">
                  Set operating hours for the bank
                </p>
              </div>
              <div className="mt-5 md:mt-0 md:col-span-2">
                <div className="grid grid-cols-6 gap-6">
                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="bank_hours_start" className="block text-sm font-medium text-gray-700">
                      Opening Time
                    </label>
                    <input
                      type="time"
                      id="bank_hours_start"
                      value={config.bank_hours_start}
                      onChange={(e) => handleInputChange('bank_hours_start', e.target.value)}
                      className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>

                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="bank_hours_end" className="block text-sm font-medium text-gray-700">
                      Closing Time
                    </label>
                    <input
                      type="time"
                      id="bank_hours_end"
                      value={config.bank_hours_end}
                      onChange={(e) => handleInputChange('bank_hours_end', e.target.value)}
                      className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="bg-indigo-600 border border-transparent rounded-md shadow-sm py-2 px-4 inline-flex justify-center text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
