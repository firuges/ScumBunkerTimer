import React, { useState, useEffect } from 'react';
import { FameReward, FameRewardCreate } from '../../api/famePoints';

interface FameRewardFormProps {
  reward?: FameReward;
  onSave: (data: FameRewardCreate) => void;
  onCancel: () => void;
  loading?: boolean;
}

const FameRewardForm: React.FC<FameRewardFormProps> = ({ 
  reward, 
  onSave, 
  onCancel, 
  loading = false 
}) => {
  const [formData, setFormData] = useState<FameRewardCreate>({
    fame_amount: 0,
    reward_description: '',
    reward_value: '',
    is_active: true
  });

  // Pre-fill form if editing
  useEffect(() => {
    if (reward) {
      setFormData({
        fame_amount: reward.fame_amount,
        reward_description: reward.reward_description,
        reward_value: reward.reward_value,
        is_active: reward.is_active
      });
    }
  }, [reward]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    const finalValue = type === 'checkbox' ? (e.target as HTMLInputElement).checked : value;
    
    setFormData(prev => ({
      ...prev,
      [name]: name === 'fame_amount' ? parseInt(finalValue as string) || 0 : finalValue
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Fame Amount */}
      <div>
        <label htmlFor="fame_amount" className="block text-sm font-medium text-gray-700 mb-1">
          Fame Points Required
        </label>
        <input
          type="number"
          id="fame_amount"
          name="fame_amount"
          value={formData.fame_amount}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="e.g. 100"
          required
          min="1"
        />
      </div>

      {/* Reward Description */}
      <div>
        <label htmlFor="reward_description" className="block text-sm font-medium text-gray-700 mb-1">
          Reward Description
        </label>
        <input
          type="text"
          id="reward_description"
          name="reward_description"
          value={formData.reward_description}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="e.g. Daily Login Bonus"
          required
          maxLength={100}
        />
      </div>

      {/* Reward Value */}
      <div>
        <label htmlFor="reward_value" className="block text-sm font-medium text-gray-700 mb-1">
          Reward Details
        </label>
        <textarea
          id="reward_value"
          name="reward_value"
          value={formData.reward_value}
          onChange={handleChange}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="e.g. 50 coins + exclusive badge"
          required
          maxLength={200}
        />
        <p className="mt-1 text-sm text-gray-500">Describe what the user will receive as a reward</p>
      </div>

      {/* Active Status */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="is_active"
          name="is_active"
          checked={formData.is_active}
          onChange={handleChange}
          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
        />
        <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
          Active (users can claim this reward)
        </label>
      </div>

      {/* Buttons */}
      <div className="flex justify-end space-x-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {loading ? 'Saving...' : (reward ? 'Update Reward' : 'Create Reward')}
        </button>
      </div>
    </form>
  );
};

export default FameRewardForm;