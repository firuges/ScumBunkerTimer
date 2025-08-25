import React, { useState, useEffect } from 'react';
import { 
  CubeIcon,
  ServerIcon,
  MapPinIcon,
  ClockIcon,
  ChartBarIcon,
  PlusIcon,
  TrashIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Modal from '../components/ui/Modal';
import { 
  bunkersAPI,
  ServerInfo,
  SectorInfo,
  BunkerRegistration,
  CreateServerRequest,
  CreateSectorRequest,
  RegisterBunkerRequest,
  BunkersOverview
} from '../api/bunkers';

export const BunkersConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Data states
  const [overview, setOverview] = useState<BunkersOverview | null>(null);
  const [servers, setServers] = useState<ServerInfo[]>([]);
  const [sectors, setSectors] = useState<SectorInfo[]>([]);
  const [registrations, setRegistrations] = useState<BunkerRegistration[]>([]);
  
  // Filter states
  const [selectedServer, setSelectedServer] = useState<string>('');

  // Modal states
  const [showServerModal, setShowServerModal] = useState(false);
  const [showSectorModal, setShowSectorModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  
  // Form states
  const [serverForm, setServerForm] = useState<CreateServerRequest>({
    guild_id: 'DEFAULT_GUILD',
    name: '',
    display_name: '',
    description: '',
    max_bunkers: 100
  });

  const [sectorForm, setSectorForm] = useState<CreateSectorRequest>({
    guild_id: 'DEFAULT_GUILD',
    sector: '',
    name: '',
    coordinates: '',
    description: '',
    default_duration_hours: 24
  });

  const [registerForm, setRegisterForm] = useState<RegisterBunkerRequest>({
    guild_id: 'DEFAULT_GUILD',
    server_name: '',
    sector: '',
    hours: 24,
    minutes: 0,
    registered_by: 'Admin Panel'
  });

  // Load data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [overviewData, serversData, sectorsData, registrationsData] = await Promise.all([
        bunkersAPI.getOverview(),
        bunkersAPI.getServers(),
        bunkersAPI.getSectors(),
        bunkersAPI.getRegistrations()
      ]);
      
      setOverview(overviewData);
      setServers(serversData);
      setSectors(sectorsData);
      setRegistrations(registrationsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bunkers data');
    } finally {
      setLoading(false);
    }
  };

  // Server management
  const handleCreateServer = async () => {
    try {
      await bunkersAPI.createServer(serverForm);
      setSuccess('Server created successfully');
      setShowServerModal(false);
      resetServerForm();
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create server');
    }
  };

  const handleDeleteServer = async (serverId: number, serverName: string) => {
    if (!window.confirm(`Are you sure you want to delete server "${serverName}" and all its bunkers?`)) {
      return;
    }
    
    try {
      await bunkersAPI.deleteServer(serverId);
      setSuccess('Server deleted successfully');
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete server');
    }
  };

  const resetServerForm = () => {
    setServerForm({
      guild_id: 'DEFAULT_GUILD',
      name: '',
      display_name: '',
      description: '',
      max_bunkers: 100
    });
  };

  // Sector management
  const handleCreateSector = async () => {
    try {
      await bunkersAPI.createSector(sectorForm);
      setSuccess('Sector created successfully');
      setShowSectorModal(false);
      resetSectorForm();
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create sector');
    }
  };

  const handleDeleteSector = async (sectorId: number, sectorName: string) => {
    if (!window.confirm(`Are you sure you want to delete sector "${sectorName}" and all its registrations?`)) {
      return;
    }
    
    try {
      await bunkersAPI.deleteSector(sectorId);
      setSuccess('Sector deleted successfully');
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete sector');
    }
  };

  const resetSectorForm = () => {
    setSectorForm({
      guild_id: 'DEFAULT_GUILD',
      sector: '',
      name: '',
      coordinates: '',
      description: '',
      default_duration_hours: 24
    });
  };

  // Registration management
  const handleRegisterBunker = async () => {
    try {
      await bunkersAPI.registerBunker(registerForm);
      setSuccess('Bunker registered successfully');
      setShowRegisterModal(false);
      resetRegisterForm();
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to register bunker');
    }
  };

  const handleCancelRegistration = async (bunkerId: number, sector: string) => {
    if (!window.confirm(`Are you sure you want to cancel registration for bunker "${sector}"?`)) {
      return;
    }
    
    try {
      await bunkersAPI.cancelRegistration(bunkerId);
      setSuccess('Bunker registration cancelled');
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel registration');
    }
  };

  const resetRegisterForm = () => {
    setRegisterForm({
      guild_id: 'DEFAULT_GUILD',
      server_name: '',
      sector: '',
      hours: 24,
      minutes: 0,
      registered_by: 'Admin Panel'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'near_expiry': return 'text-yellow-600 bg-yellow-100';
      case 'expired': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatTimeRemaining = (registration: BunkerRegistration) => {
    if (registration.time_remaining) {
      return registration.time_remaining;
    }
    if (registration.expired_minutes_ago !== undefined) {
      const hours = Math.floor(registration.expired_minutes_ago / 60);
      const minutes = registration.expired_minutes_ago % 60;
      return `${hours}h ${minutes}m ago`;
    }
    return 'Unknown';
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <CubeIcon className="w-8 h-8 mr-3" />
          Bunkers Management
        </h1>
        <p className="text-gray-600 mt-2">
          Configure servers, sectors, and manage bunker registrations
        </p>
      </div>

      {/* Notifications */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-300 text-red-700 rounded-lg flex items-center">
          <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">×</button>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-100 border border-green-300 text-green-700 rounded-lg flex items-center">
          <CheckCircleIcon className="w-5 h-5 mr-2" />
          {success}
          <button onClick={() => setSuccess(null)} className="ml-auto text-green-500 hover:text-green-700">×</button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: ChartBarIcon },
            { id: 'servers', label: 'Servers', icon: ServerIcon },
            { id: 'sectors', label: 'Sectors', icon: MapPinIcon },
            { id: 'registrations', label: 'Registrations', icon: ClockIcon }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 bg-blue-50'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm flex items-center transition-colors`}
            >
              <tab.icon className="w-5 h-5 mr-2" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && overview && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow border">
              <div className="flex items-center">
                <ServerIcon className="w-8 h-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Servers</p>
                  <p className="text-2xl font-bold text-gray-900">{overview.stats.total_servers}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow border">
              <div className="flex items-center">
                <MapPinIcon className="w-8 h-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Sectors</p>
                  <p className="text-2xl font-bold text-gray-900">{overview.stats.total_sectors}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow border">
              <div className="flex items-center">
                <CubeIcon className="w-8 h-8 text-purple-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Active Bunkers</p>
                  <p className="text-2xl font-bold text-gray-900">{overview.stats.active_registrations}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow border">
              <div className="flex items-center">
                <ChartBarIcon className="w-8 h-8 text-yellow-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Registrations</p>
                  <p className="text-2xl font-bold text-gray-900">{overview.stats.total_registrations}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow border">
              <div className="flex items-center">
                <ClockIcon className="w-8 h-8 text-indigo-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Today's Registrations</p>
                  <p className="text-2xl font-bold text-gray-900">{overview.stats.registrations_today}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow border">
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  overview.health === 'healthy' ? 'bg-green-500' : 
                  overview.health === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                }`}>
                  <span className="text-white text-sm font-bold">
                    {overview.health === 'healthy' ? '✓' : '⚠'}
                  </span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">System Health</p>
                  <p className="text-lg font-bold capitalize text-gray-900">{overview.health}</p>
                </div>
              </div>
            </div>
          </div>

          {overview.stats.most_active_sector && (
            <div className="bg-white p-6 rounded-lg shadow border">
              <h3 className="text-lg font-semibold mb-2">Most Active Sector</h3>
              <p className="text-2xl font-bold text-blue-600">{overview.stats.most_active_sector}</p>
              <p className="text-gray-600">This week</p>
            </div>
          )}
        </div>
      )}

      {/* Servers Tab */}
      {activeTab === 'servers' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Server Configuration</h2>
            <button
              onClick={() => setShowServerModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center transition-colors"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add Server
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {servers.map(server => (
              <div key={server.id} className="bg-white p-6 rounded-lg shadow border">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{server.display_name}</h3>
                    <p className="text-sm text-gray-600">{server.name}</p>
                    {server.description && (
                      <p className="text-sm text-gray-500 mt-1">{server.description}</p>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeleteServer(server.id, server.display_name)}
                    className="text-red-600 hover:text-red-800 transition-colors"
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-600">Max Bunkers:</span>
                    <span className="ml-2">{server.max_bunkers}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Total:</span>
                    <span className="ml-2">{server.total_bunkers}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Active:</span>
                    <span className="ml-2 text-green-600">{server.active_bunkers}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Status:</span>
                    <span className={`ml-2 px-2 py-1 rounded text-xs ${
                      server.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {server.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sectors Tab */}
      {activeTab === 'sectors' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Bunker Sectors</h2>
            <button
              onClick={() => setShowSectorModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center transition-colors"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add Sector
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sectors.map(sector => (
              <div key={sector.id} className="bg-white p-6 rounded-lg shadow border">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{sector.sector}</h3>
                    <p className="text-sm text-gray-600">{sector.name}</p>
                    {sector.coordinates && (
                      <p className="text-xs text-gray-500">{sector.coordinates}</p>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeleteSector(sector.id, sector.sector)}
                    className="text-red-600 hover:text-red-800 transition-colors"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>

                {sector.description && (
                  <p className="text-sm text-gray-600 mb-3">{sector.description}</p>
                )}

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Default Duration:</span>
                    <span>{sector.default_duration_hours}h</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Registrations:</span>
                    <span>{sector.total_registrations}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Active:</span>
                    <span className="text-green-600">{sector.active_registrations}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      sector.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {sector.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Registrations Tab */}
      {activeTab === 'registrations' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Bunker Registrations</h2>
            <div className="flex space-x-4">
              <select
                value={selectedServer}
                onChange={(e) => setSelectedServer(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="">All Servers</option>
                {servers.map(server => (
                  <option key={server.id} value={server.name}>
                    {server.display_name}
                  </option>
                ))}
              </select>
              <button
                onClick={() => setShowRegisterModal(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center transition-colors"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                Register Bunker
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sector</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Server</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time Remaining</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Registered By</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {registrations
                  .filter(reg => !selectedServer || reg.server_name === selectedServer)
                  .map(registration => (
                  <tr key={registration.id}>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {registration.sector}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {registration.server_name}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(registration.status)}`}>
                        {registration.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatTimeRemaining(registration)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {registration.registered_by}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleCancelRegistration(registration.id, registration.sector)}
                        className="text-red-600 hover:text-red-800 transition-colors"
                        title="Cancel Registration"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {registrations.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No bunker registrations found
              </div>
            )}
          </div>
        </div>
      )}

      {/* Server Creation Modal */}
      <Modal
        isOpen={showServerModal}
        onClose={() => setShowServerModal(false)}
        title="Add New Server"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Server Name
            </label>
            <input
              type="text"
              value={serverForm.name}
              onChange={(e) => setServerForm({...serverForm, name: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              placeholder="e.g., scum-server-1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Display Name
            </label>
            <input
              type="text"
              value={serverForm.display_name}
              onChange={(e) => setServerForm({...serverForm, display_name: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              placeholder="e.g., SCUM Server #1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={serverForm.description}
              onChange={(e) => setServerForm({...serverForm, description: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 h-20"
              placeholder="Server description (optional)"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Bunkers
            </label>
            <input
              type="number"
              value={serverForm.max_bunkers}
              onChange={(e) => setServerForm({...serverForm, max_bunkers: parseInt(e.target.value) || 100})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              min="1"
              max="1000"
            />
          </div>

          <div className="flex justify-end space-x-4 pt-4">
            <button
              onClick={() => setShowServerModal(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateServer}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Server
            </button>
          </div>
        </div>
      </Modal>

      {/* Sector Creation Modal */}
      <Modal
        isOpen={showSectorModal}
        onClose={() => setShowSectorModal(false)}
        title="Add New Sector"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sector Code
            </label>
            <input
              type="text"
              value={sectorForm.sector}
              onChange={(e) => setSectorForm({...sectorForm, sector: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              placeholder="e.g., A1, B2, C3"
              maxLength={10}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sector Name
            </label>
            <input
              type="text"
              value={sectorForm.name}
              onChange={(e) => setSectorForm({...sectorForm, name: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              placeholder="e.g., Alpha Sector A1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Coordinates
            </label>
            <input
              type="text"
              value={sectorForm.coordinates}
              onChange={(e) => setSectorForm({...sectorForm, coordinates: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              placeholder="e.g., 1500,2300 (optional)"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={sectorForm.description}
              onChange={(e) => setSectorForm({...sectorForm, description: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 h-20"
              placeholder="Sector description (optional)"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Duration (hours)
            </label>
            <input
              type="number"
              value={sectorForm.default_duration_hours}
              onChange={(e) => setSectorForm({...sectorForm, default_duration_hours: parseInt(e.target.value) || 24})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              min="1"
              max="168"
            />
          </div>

          <div className="flex justify-end space-x-4 pt-4">
            <button
              onClick={() => setShowSectorModal(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateSector}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Sector
            </button>
          </div>
        </div>
      </Modal>

      {/* Bunker Registration Modal */}
      <Modal
        isOpen={showRegisterModal}
        onClose={() => setShowRegisterModal(false)}
        title="Register Bunker"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Server
            </label>
            <select
              value={registerForm.server_name}
              onChange={(e) => setRegisterForm({...registerForm, server_name: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              required
            >
              <option value="">Select a server</option>
              {servers.filter(s => s.is_active).map(server => (
                <option key={server.id} value={server.name}>
                  {server.display_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sector
            </label>
            <select
              value={registerForm.sector}
              onChange={(e) => setRegisterForm({...registerForm, sector: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              required
            >
              <option value="">Select a sector</option>
              {sectors.filter(s => s.is_active).map(sector => (
                <option key={sector.id} value={sector.sector}>
                  {sector.sector} - {sector.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hours
              </label>
              <input
                type="number"
                value={registerForm.hours}
                onChange={(e) => setRegisterForm({...registerForm, hours: parseInt(e.target.value) || 0})}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min="0"
                max="168"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minutes
              </label>
              <input
                type="number"
                value={registerForm.minutes}
                onChange={(e) => setRegisterForm({...registerForm, minutes: parseInt(e.target.value) || 0})}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min="0"
                max="59"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Registered By
            </label>
            <input
              type="text"
              value={registerForm.registered_by}
              onChange={(e) => setRegisterForm({...registerForm, registered_by: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              placeholder="Admin name or identifier"
            />
          </div>

          <div className="flex justify-end space-x-4 pt-4">
            <button
              onClick={() => setShowRegisterModal(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleRegisterBunker}
              disabled={!registerForm.server_name || !registerForm.sector}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Register Bunker
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};