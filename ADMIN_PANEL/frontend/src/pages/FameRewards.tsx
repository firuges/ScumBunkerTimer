import React, { useState, useEffect } from 'react';
import { PlusIcon, PencilIcon, TrashIcon, EyeIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Modal from '../components/ui/Modal';
import FameRewardForm from '../components/forms/FameRewardForm';
import { famePointsAPI, FameReward } from '../api/famePoints';

export const FameRewards: React.FC = () => {
  const [rewards, setRewards] = useState<FameReward[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingReward, setEditingReward] = useState<FameReward | null>(null);

  // Mock guild ID - in real app this would come from auth context
  const guildId = '123456789';

  // Load rewards from API
  useEffect(() => {
    loadRewards();
  }, []);

  const loadRewards = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await famePointsAPI.getRewards(guildId);
      setRewards(data);
    } catch (err: any) {
      console.error('Error loading rewards:', err);
      setError('Failed to load rewards. Please try again.');
      // Fallback to empty array
      setRewards([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingReward(null);
    setShowModal(true);
  };

  const handleEdit = (reward: FameReward) => {
    setEditingReward(reward);
    setShowModal(true);
  };

  const handleDelete = async (reward: FameReward) => {
    if (!window.confirm(`¿Estás seguro de eliminar la recompensa "${reward.reward_description}"?`)) {
      return;
    }

    try {
      await famePointsAPI.deleteReward(guildId, reward.id!);
      // Refresh the list
      await loadRewards();
    } catch (err: any) {
      console.error('Error deleting reward:', err);
      setError('Failed to delete reward. Please try again.');
    }
  };

  const handleSave = async (rewardData: any) => {
    try {
      if (editingReward) {
        // Update existing reward
        await famePointsAPI.updateReward(guildId, editingReward.id!, rewardData);
      } else {
        // Create new reward
        await famePointsAPI.createReward(guildId, rewardData);
      }
      
      // Refresh the list and close modal
      await loadRewards();
      setShowModal(false);
      setEditingReward(null);
    } catch (err: any) {
      console.error('Error saving reward:', err);
      setError('Failed to save reward. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="py-6">
        {/* Error message */}
        {error && (
          <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
            <span className="block sm:inline">{error}</span>
            <span
              className="absolute top-0 bottom-0 right-0 px-4 py-3 cursor-pointer"
              onClick={() => setError(null)}
            >
              <svg className="fill-current h-6 w-6 text-red-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                <title>Close</title>
                <path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/>
              </svg>
            </span>
          </div>
        )}
        <div className="md:flex md:items-center md:justify-between mb-8">
          <div className="flex-1 min-w-0">
            <h1 className="text-3xl font-bold text-gray-900">Fame Points Rewards</h1>
            <p className="mt-2 text-sm text-gray-600">
              Gestiona las recompensas de Fame Points para tu servidor
            </p>
          </div>
          <div className="mt-4 flex md:mt-0 md:ml-4">
            <button
              onClick={handleCreate}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Nueva Recompensa
            </button>
          </div>
        </div>

        {/* Modal for Create/Edit */}
        <Modal
          isOpen={showModal}
          onClose={() => {
            setShowModal(false);
            setEditingReward(null);
          }}
          title={editingReward ? 'Editar Recompensa' : 'Nueva Recompensa'}
        >
          <FameRewardForm
            reward={editingReward}
            onSave={handleSave}
            onCancel={() => {
              setShowModal(false);
              setEditingReward(null);
            }}
          />
        </Modal>

        {/* Rewards Table */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {rewards.map((reward) => (
              <li key={reward.id}>
                <div className="px-4 py-4 flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        reward.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {reward.is_active ? 'Activa' : 'Inactiva'}
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900">
                          {reward.reward_description}
                        </p>
                        <div className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                          {reward.fame_amount} Fame Points
                        </div>
                      </div>
                      <p className="text-sm text-gray-500">{reward.reward_value}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleEdit(reward)}
                      className="text-indigo-600 hover:text-indigo-900"
                      title="Editar"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      className="text-blue-600 hover:text-blue-900"
                      title="Preview"
                    >
                      <EyeIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(reward)}
                      className="text-red-600 hover:text-red-900"
                      title="Eliminar"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {rewards.length === 0 && (
          <div className="text-center py-12">
            <div className="mx-auto h-12 w-12 text-gray-400">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </div>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No hay recompensas</h3>
            <p className="mt-1 text-sm text-gray-500">Comienza creando tu primera recompensa de Fame Points.</p>
            <div className="mt-6">
              <button
                onClick={handleCreate}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Nueva Recompensa
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};