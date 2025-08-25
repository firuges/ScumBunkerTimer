import React, { useState, useEffect } from 'react';
import { 
  CogIcon, 
  TruckIcon, 
  MapPinIcon,
  CalculatorIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { 
  taxiAPI, 
  TaxiConfig as TaxiConfigType, 
  TaxiConfigUpdate,
  Vehicle,
  TaxiZone,
  TaxiStop,
  DriverLevel,
  FareCalculationRequest,
  FareCalculationResponse 
} from '../api/taxi';

export const TaxiConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('config');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Data states
  const [config, setConfig] = useState<TaxiConfigType | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [zones, setZones] = useState<TaxiZone[]>([]);
  const [stops, setStops] = useState<TaxiStop[]>([]);
  const [driverLevels, setDriverLevels] = useState<DriverLevel[]>([]);

  // Fare calculator states
  const [fareRequest, setFareRequest] = useState<FareCalculationRequest>({
    origin_x: 0,
    origin_y: 0,
    destination_x: 1500,
    destination_y: 2300,
    vehicle_type: 'hatchback',
    zone_type: 'safe',
    driver_level: 1,
    is_night_time: false,
    is_peak_hours: false,
  });
  const [fareResult, setFareResult] = useState<FareCalculationResponse | null>(null);
  const [calculating, setCalculating] = useState(false);
  const [editingConfig, setEditingConfig] = useState(false);
  
  // Zone modal states
  const [showZoneModal, setShowZoneModal] = useState(false);
  const [editingZone, setEditingZone] = useState<TaxiZone | null>(null);
  const [zoneFormData, setZoneFormData] = useState({
    zone_name: '',
    display_name: '',
    description: '',
    zone_type: 'safe_zone',
    danger_multiplier: 1.0,
    min_driver_level: 1,
    allowed_vehicles: 'auto,moto',
    restricted_hours: '',
    coordinate_bounds: '',
    warning_message: '',
    requires_confirmation: false,
    is_active: true
  });
  
  // Stop modal states
  const [showStopModal, setShowStopModal] = useState(false);
  const [editingStop, setEditingStop] = useState<TaxiStop | null>(null);
  const [stopFormData, setStopFormData] = useState({
    stop_name: '',
    display_name: '',
    description: '',
    coordinate_x: 0,
    coordinate_y: 0,
    coordinate_z: 0,
    zone_id: undefined as number | undefined,
    is_pickup_point: true,
    is_dropoff_point: true,
    popularity_bonus: 1.0,
    waiting_area_size: 5,
    landmark_type: 'town_stop',
    emoji: '🚕',
    is_active: true
  });
  const [configChanges, setConfigChanges] = useState<TaxiConfigUpdate | null>(null);
  const [showVehicleModal, setShowVehicleModal] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [vehicleFormData, setVehicleFormData] = useState({
    vehicle_name: '',
    display_name: '',
    description: '',
    emoji: '🚗',
    base_multiplier: 1.0,
    capacity_passengers: 4,
    unlock_level: 1,
    is_premium: false
  });

  const guildId = '123456789';

  const tabs = [
    { id: 'config', name: 'Configuration', icon: CogIcon },
    { id: 'vehicles', name: 'Vehicles', icon: TruckIcon },
    { id: 'zones', name: 'Zones & Stops', icon: MapPinIcon },
    { id: 'calculator', name: 'Fare Calculator', icon: CalculatorIcon },
    { id: 'levels', name: 'Driver Levels', icon: ChartBarIcon },
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        configData,
        vehiclesData,
        zonesData,
        stopsData,
        driverLevelsData
      ] = await Promise.all([
        taxiAPI.getConfig(guildId),
        taxiAPI.getVehicles(guildId),
        taxiAPI.getZones(guildId),
        taxiAPI.getStops(guildId),
        taxiAPI.getDriverLevels(guildId)
      ]);

      setConfig(configData);
      setVehicles(vehiclesData);
      setZones(zonesData);
      setStops(stopsData);
      setDriverLevels(driverLevelsData);

    } catch (err: any) {
      setError(err.message || 'Error loading taxi data');
    } finally {
      setLoading(false);
    }
  };

  const handleCalculateFare = async () => {
    try {
      setCalculating(true);
      const result = await taxiAPI.calculateFare(fareRequest, guildId);
      setFareResult(result);
    } catch (err: any) {
      setError(err.message || 'Error calculating fare');
    } finally {
      setCalculating(false);
    }
  };

  const handleEditConfig = () => {
    if (config) {
      setConfigChanges({
        taxi_channel_id: config.taxi_channel_id,
        base_fare: config.base_fare,
        per_km_rate: config.per_km_rate,
        commission_percent: config.commission_percent,
        max_distance_km: config.max_distance_km,
        min_fare: config.min_fare,
        waiting_time_rate: config.waiting_time_rate,
        night_multiplier: config.night_multiplier,
        peak_hours_multiplier: config.peak_hours_multiplier,
        peak_hours_start: config.peak_hours_start,
        peak_hours_end: config.peak_hours_end,
        auto_accept_distance: config.auto_accept_distance,
        driver_minimum_level: config.driver_minimum_level,
        is_active: config.is_active
      });
      setEditingConfig(true);
    }
  };

  const handleSaveConfig = async () => {
    if (!configChanges) return;
    
    try {
      setLoading(true);
      setError(null);
      const updatedConfig = await taxiAPI.updateConfig(guildId, configChanges);
      setConfig(updatedConfig);
      setEditingConfig(false);
      setConfigChanges(null);
      setSuccess('Configuración actualizada correctamente');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Error updating configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingConfig(false);
    setConfigChanges(null);
  };

  const handleCreateVehicle = () => {
    setEditingVehicle(null);
    setVehicleFormData({
      vehicle_name: '',
      display_name: '',
      description: '',
      emoji: '🚗',
      base_multiplier: 1.0,
      capacity_passengers: 4,
      unlock_level: 1,
      is_premium: false
    });
    setShowVehicleModal(true);
  };

  const handleEditVehicle = (vehicle: Vehicle) => {
    setEditingVehicle(vehicle);
    setVehicleFormData({
      vehicle_name: vehicle.vehicle_name,
      display_name: vehicle.display_name,
      description: vehicle.description || '',
      emoji: vehicle.emoji,
      base_multiplier: vehicle.base_multiplier,
      capacity_passengers: vehicle.capacity_passengers,
      unlock_level: vehicle.unlock_level,
      is_premium: vehicle.is_premium
    });
    setShowVehicleModal(true);
  };

  const handleSaveVehicle = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (editingVehicle) {
        // Update existing vehicle
        await taxiAPI.updateVehicle(editingVehicle.id!, vehicleFormData, guildId);
        setSuccess('Vehículo actualizado correctamente');
      } else {
        // Create new vehicle
        await taxiAPI.createVehicle(vehicleFormData, guildId);
        setSuccess('Vehículo creado correctamente');
      }
      
      await loadData();
      setShowVehicleModal(false);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Error saving vehicle');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteVehicle = async (vehicleId: number) => {
    // eslint-disable-next-line no-restricted-globals
    if (!confirm('¿Estás seguro de que quieres eliminar este vehículo?')) return;
    
    try {
      setLoading(true);
      setError(null);
      await taxiAPI.deleteVehicle(vehicleId, guildId);
      await loadData();
      setSuccess('Vehículo eliminado correctamente');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Error deleting vehicle');
    } finally {
      setLoading(false);
    }
  };

  // Zone management functions
  const openZoneModal = (zone?: TaxiZone) => {
    if (zone) {
      setEditingZone(zone);
      setZoneFormData({
        zone_name: zone.zone_name,
        display_name: zone.display_name,
        description: zone.description || '',
        zone_type: zone.zone_type,
        danger_multiplier: zone.danger_multiplier,
        min_driver_level: zone.min_driver_level,
        allowed_vehicles: zone.allowed_vehicles,
        restricted_hours: zone.restricted_hours || '',
        coordinate_bounds: zone.coordinate_bounds || '',
        warning_message: zone.warning_message || '',
        requires_confirmation: zone.requires_confirmation,
        is_active: zone.is_active
      });
    } else {
      setEditingZone(null);
      setZoneFormData({
        zone_name: '',
        display_name: '',
        description: '',
        zone_type: 'safe_zone',
        danger_multiplier: 1.0,
        min_driver_level: 1,
        allowed_vehicles: 'auto,moto',
        restricted_hours: '',
        coordinate_bounds: '',
        warning_message: '',
        requires_confirmation: false,
        is_active: true
      });
    }
    setShowZoneModal(true);
  };

  const handleSaveZone = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      
      const zoneData = { ...zoneFormData, guild_id: guildId };
      
      if (editingZone) {
        await taxiAPI.updateZone(editingZone.id!, zoneData, guildId);
        setSuccess('Zona actualizada correctamente');
      } else {
        await taxiAPI.createZone(zoneData);
        setSuccess('Zona creada correctamente');
      }
      
      await loadData();
      setShowZoneModal(false);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Error saving zone');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteZone = async (zoneId: number) => {
    // eslint-disable-next-line no-restricted-globals
    if (!confirm('¿Estás seguro de que quieres eliminar esta zona?')) return;
    
    try {
      setLoading(true);
      setError(null);
      await taxiAPI.deleteZone(zoneId, guildId);
      await loadData();
      setSuccess('Zona eliminada correctamente');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Error deleting zone');
    } finally {
      setLoading(false);
    }
  };

  // Stop management functions
  const openStopModal = (stop?: TaxiStop) => {
    if (stop) {
      setEditingStop(stop);
      setStopFormData({
        stop_name: stop.stop_name,
        display_name: stop.display_name,
        description: stop.description || '',
        coordinate_x: stop.coordinate_x,
        coordinate_y: stop.coordinate_y,
        coordinate_z: stop.coordinate_z,
        zone_id: stop.zone_id,
        is_pickup_point: stop.is_pickup_point,
        is_dropoff_point: stop.is_dropoff_point,
        popularity_bonus: stop.popularity_bonus,
        waiting_area_size: stop.waiting_area_size,
        landmark_type: stop.landmark_type,
        emoji: stop.emoji,
        is_active: stop.is_active
      });
    } else {
      setEditingStop(null);
      setStopFormData({
        stop_name: '',
        display_name: '',
        description: '',
        coordinate_x: 0,
        coordinate_y: 0,
        coordinate_z: 0,
        zone_id: undefined,
        is_pickup_point: true,
        is_dropoff_point: true,
        popularity_bonus: 1.0,
        waiting_area_size: 5,
        landmark_type: 'town_stop',
        emoji: '🚕',
        is_active: true
      });
    }
    setShowStopModal(true);
  };

  const handleSaveStop = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      
      const stopData = { ...stopFormData, guild_id: guildId };
      
      if (editingStop) {
        await taxiAPI.updateStop(editingStop.id!, stopData, guildId);
        setSuccess('Parada actualizada correctamente');
      } else {
        await taxiAPI.createStop(stopData);
        setSuccess('Parada creada correctamente');
      }
      
      await loadData();
      setShowStopModal(false);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Error saving stop');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteStop = async (stopId: number) => {
    // eslint-disable-next-line no-restricted-globals
    if (!confirm('¿Estás seguro de que quieres eliminar esta parada?')) return;
    
    try {
      setLoading(true);
      setError(null);
      await taxiAPI.deleteStop(stopId, guildId);
      await loadData();
      setSuccess('Parada eliminada correctamente');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Error deleting stop');
    } finally {
      setLoading(false);
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Configuración del Sistema Taxi</h1>
          <p className="mt-2 text-sm text-gray-600">
            Configura vehículos, zonas, precios y simula costos del sistema taxi
          </p>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-sm text-red-600">{error}</div>
          </div>
        )}

        {success && (
          <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="text-sm text-green-600">{success}</div>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
              >
                <tab.icon className="h-4 w-4 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow p-6">
          {activeTab === 'config' && config && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Configuración General</h2>
                  <p className="text-gray-600 mt-1">Ajustes principales del sistema taxi</p>
                </div>
                <div className="flex space-x-2">
                  {editingConfig ? (
                    <>
                      <button
                        onClick={handleCancelEdit}
                        className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                      >
                        Cancelar
                      </button>
                      <button
                        onClick={handleSaveConfig}
                        className="px-4 py-2 bg-indigo-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-indigo-700"
                      >
                        Guardar Cambios
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={handleEditConfig}
                      className="px-4 py-2 bg-indigo-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-indigo-700"
                    >
                      Editar Configuración
                    </button>
                  )}
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tarifa Base
                    </label>
                    <input
                      type="number"
                      value={editingConfig ? configChanges?.base_fare || 0 : config.base_fare}
                      onChange={(e) => editingConfig && configChanges && setConfigChanges({...configChanges, base_fare: parseFloat(e.target.value) || 0})}
                      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                        editingConfig ? 'bg-white' : 'bg-gray-50'
                      }`}
                      readOnly={!editingConfig}
                    />
                    <p className="text-xs text-gray-500 mt-1">Costo inicial por viaje</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tarifa por Kilómetro
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={editingConfig ? configChanges?.per_km_rate || 0 : config.per_km_rate}
                      onChange={(e) => editingConfig && configChanges && setConfigChanges({...configChanges, per_km_rate: parseFloat(e.target.value) || 0})}
                      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                        editingConfig ? 'bg-white' : 'bg-gray-50'
                      }`}
                      readOnly={!editingConfig}
                    />
                    <p className="text-xs text-gray-500 mt-1">Costo por cada kilómetro</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Comisión del Sistema (%)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="100"
                      value={editingConfig ? configChanges?.commission_percent || 0 : config.commission_percent}
                      onChange={(e) => editingConfig && configChanges && setConfigChanges({...configChanges, commission_percent: parseFloat(e.target.value) || 0})}
                      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                        editingConfig ? 'bg-white' : 'bg-gray-50'
                      }`}
                      readOnly={!editingConfig}
                    />
                    <p className="text-xs text-gray-500 mt-1">Porcentaje que se queda el sistema</p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Multiplicador Nocturno
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="1"
                      value={editingConfig ? configChanges?.night_multiplier || 1 : config.night_multiplier}
                      onChange={(e) => editingConfig && configChanges && setConfigChanges({...configChanges, night_multiplier: parseFloat(e.target.value) || 1})}
                      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                        editingConfig ? 'bg-white' : 'bg-gray-50'
                      }`}
                      readOnly={!editingConfig}
                    />
                    <p className="text-xs text-gray-500 mt-1">Multiplicador durante la noche</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Multiplicador Horas Pico
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="1"
                      value={editingConfig ? configChanges?.peak_hours_multiplier || 1 : config.peak_hours_multiplier}
                      onChange={(e) => editingConfig && configChanges && setConfigChanges({...configChanges, peak_hours_multiplier: parseFloat(e.target.value) || 1})}
                      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                        editingConfig ? 'bg-white' : 'bg-gray-50'
                      }`}
                      readOnly={!editingConfig}
                    />
                    <p className="text-xs text-gray-500 mt-1">Multiplicador en horas pico</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tarifa Mínima
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={editingConfig ? configChanges?.min_fare || 0 : config.min_fare}
                      onChange={(e) => editingConfig && configChanges && setConfigChanges({...configChanges, min_fare: parseFloat(e.target.value) || 0})}
                      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                        editingConfig ? 'bg-white' : 'bg-gray-50'
                      }`}
                      readOnly={!editingConfig}
                    />
                    <p className="text-xs text-gray-500 mt-1">Mínimo a cobrar por viaje</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'vehicles' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Gestión de Vehículos</h2>
                  <p className="text-gray-600 mt-1">Configura los tipos de vehículos disponibles y sus multiplicadores</p>
                </div>
                <button
                  onClick={handleCreateVehicle}
                  className="px-4 py-2 bg-indigo-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-indigo-700"
                >
                  + Crear Vehículo
                </button>
              </div>
              
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {vehicles.map((vehicle) => (
                  <div key={vehicle.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <span className="text-lg mr-2">{vehicle.emoji}</span>
                      <h3 className="font-medium text-gray-900">{vehicle.display_name}</h3>
                    </div>
                    <p className="text-sm text-gray-500 mb-3">{vehicle.description}</p>
                    <div className="space-y-1 text-xs text-gray-600">
                      <div className="flex justify-between">
                        <span>Multiplicador Base:</span>
                        <span>{vehicle.base_multiplier}x</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Capacidad:</span>
                        <span>{vehicle.capacity_passengers} pasajeros</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Nivel requerido:</span>
                        <span>Nivel {vehicle.unlock_level}</span>
                      </div>
                      {vehicle.is_premium && (
                        <div className="mt-2">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                            Premium
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="mt-3 flex space-x-2">
                      <button
                        onClick={() => handleEditVehicle(vehicle)}
                        className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleDeleteVehicle(vehicle.id!)}
                        className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'zones' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Zonas y Paradas</h2>
              <p className="text-gray-600 mb-6">Define zonas PVP/PVE y paradas de taxi</p>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="font-medium text-gray-900">Zonas Configuradas</h3>
                    <button
                      onClick={() => openZoneModal()}
                      className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                    >
                      + Crear Zona Grid/Pad
                    </button>
                  </div>
                  <div className="space-y-3">
                    {zones.map((zone) => (
                      <div key={zone.id} className="border border-gray-200 rounded-lg p-3">
                        <div className="flex justify-between items-center">
                          <div>
                            <span className="font-medium">{zone.display_name}</span>
                            <div className="text-sm text-gray-500">{zone.zone_type.toUpperCase()} Zone</div>
                            <div className="text-xs text-gray-400">ID: {zone.zone_name} | Multiplicador: {zone.danger_multiplier}x</div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              zone.zone_type === 'safe' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {zone.zone_type === 'safe' ? 'Segura' : 'Peligrosa'}
                            </span>
                            <button
                              onClick={() => openZoneModal(zone)}
                              className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200 mr-1"
                            >
                              Editar
                            </button>
                            <button
                              onClick={() => handleDeleteZone(zone.id)}
                              className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                            >
                              Eliminar
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="font-medium text-gray-900">Paradas de Taxi</h3>
                    <button
                      onClick={() => openStopModal()}
                      className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                    >
                      + Crear Parada
                    </button>
                  </div>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {stops.map((stop) => (
                      <div key={stop.id} className="border border-gray-200 rounded-lg p-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <span className="text-sm mr-2">{stop.emoji}</span>
                            <div>
                              <div className="font-medium text-sm">{stop.display_name}</div>
                              <div className="text-xs text-gray-500">{stop.landmark_type}</div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-1">
                            <div className="text-xs text-gray-400">
                              ({stop.coordinate_x}, {stop.coordinate_y})
                            </div>
                            <button
                              onClick={() => openStopModal(stop)}
                              className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                            >
                              Editar
                            </button>
                            <button
                              onClick={() => handleDeleteStop(stop.id)}
                              className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                            >
                              Del
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'calculator' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Calculadora de Tarifas</h2>
              <p className="text-gray-600 mb-6">Calcula costos de viajes en tiempo real</p>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Origen X
                      </label>
                      <input
                        type="number"
                        value={fareRequest.origin_x}
                        onChange={(e) => setFareRequest({...fareRequest, origin_x: parseFloat(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Origen Y
                      </label>
                      <input
                        type="number"
                        value={fareRequest.origin_y}
                        onChange={(e) => setFareRequest({...fareRequest, origin_y: parseFloat(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Destino X
                      </label>
                      <input
                        type="number"
                        value={fareRequest.destination_x}
                        onChange={(e) => setFareRequest({...fareRequest, destination_x: parseFloat(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Destino Y
                      </label>
                      <input
                        type="number"
                        value={fareRequest.destination_y}
                        onChange={(e) => setFareRequest({...fareRequest, destination_y: parseFloat(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo de Vehículo
                    </label>
                    <select 
                      value={fareRequest.vehicle_type}
                      onChange={(e) => setFareRequest({...fareRequest, vehicle_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {vehicles.map((vehicle) => (
                        <option key={vehicle.id} value={vehicle.vehicle_name}>
                          {vehicle.display_name} ({vehicle.base_multiplier}x)
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo de Zona
                    </label>
                    <select 
                      value={fareRequest.zone_type || 'safe'}
                      onChange={(e) => setFareRequest({...fareRequest, zone_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {zones.map((zone) => (
                        <option key={zone.id} value={zone.zone_type}>
                          {zone.display_name} ({zone.danger_multiplier}x)
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nivel del Conductor
                    </label>
                    <select 
                      value={fareRequest.driver_level}
                      onChange={(e) => setFareRequest({...fareRequest, driver_level: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {driverLevels.map((level) => (
                        <option key={level.id} value={level.level}>
                          {level.level_name} (Nivel {level.level})
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={fareRequest.is_night_time}
                        onChange={(e) => setFareRequest({...fareRequest, is_night_time: e.target.checked})}
                        className="mr-2"
                      />
                      <span className="text-sm">Horario nocturno</span>
                    </label>
                    
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={fareRequest.is_peak_hours}
                        onChange={(e) => setFareRequest({...fareRequest, is_peak_hours: e.target.checked})}
                        className="mr-2"
                      />
                      <span className="text-sm">Horas pico</span>
                    </label>
                  </div>
                  
                  <button 
                    onClick={handleCalculateFare}
                    disabled={calculating}
                    className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {calculating ? 'Calculando...' : 'Calcular Costo'}
                  </button>
                </div>
                
                <div className="bg-indigo-50 rounded-lg p-6">
                  <h3 className="font-semibold text-indigo-900 mb-4">Resultado del Cálculo</h3>
                  {fareResult ? (
                    <div className="space-y-3">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-indigo-600 mb-1">
                          ${fareResult.total_fare.toFixed(2)}
                        </div>
                        <div className="text-sm text-indigo-700">Costo Total del Viaje</div>
                      </div>
                      
                      <div className="border-t border-indigo-200 pt-3 space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Distancia:</span>
                          <span>{fareResult.distance_km} km</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Tarifa base:</span>
                          <span>${fareResult.base_fare.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Tarifa distancia:</span>
                          <span>${fareResult.distance_fare.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Multiplicador vehículo:</span>
                          <span>×{fareResult.vehicle_multiplier}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Multiplicador zona:</span>
                          <span>×{fareResult.zone_multiplier}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Multiplicador tiempo:</span>
                          <span>×{fareResult.time_multiplier}</span>
                        </div>
                        <div className="flex justify-between text-red-600">
                          <span>Comisión:</span>
                          <span>-${fareResult.commission.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between font-medium pt-2 border-t border-indigo-200">
                          <span>Para el conductor:</span>
                          <span>${fareResult.driver_earnings.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center text-gray-500">
                      <CalculatorIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <p>Ingresa los datos y haz clic en "Calcular Costo"</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'levels' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Niveles de Conductor</h2>
              <p className="text-gray-600 mb-6">Sistema de progresión y recompensas para conductores</p>
              
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {driverLevels.map((level) => (
                  <div key={level.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <span className="text-lg mr-2">{level.badge_emoji}</span>
                      <h3 className="font-medium text-gray-900">{level.level_name}</h3>
                    </div>
                    <div className="text-sm text-gray-600 mb-3">Nivel {level.level}</div>
                    <div className="space-y-1 text-xs text-gray-600">
                      <div className="flex justify-between">
                        <span>Viajes requeridos:</span>
                        <span>{level.required_trips}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Distancia requerida:</span>
                        <span>{level.required_distance} km</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Mult. ganancias:</span>
                        <span>×{level.earnings_multiplier}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Mult. propinas:</span>
                        <span>×{level.tip_multiplier}</span>
                      </div>
                    </div>
                    {level.description && (
                      <div className="mt-2 text-xs text-gray-500 italic">
                        {level.description}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Vehicle Modal */}
        {showVehicleModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  {editingVehicle ? 'Editar Vehículo' : 'Crear Nuevo Vehículo'}
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nombre del Vehículo
                    </label>
                    <input
                      type="text"
                      value={vehicleFormData.vehicle_name}
                      onChange={(e) => setVehicleFormData({...vehicleFormData, vehicle_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="ej: hatchback"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nombre para Mostrar
                    </label>
                    <input
                      type="text"
                      value={vehicleFormData.display_name}
                      onChange={(e) => setVehicleFormData({...vehicleFormData, display_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="ej: Hatchback Compacto"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Emoji
                      </label>
                      <input
                        type="text"
                        value={vehicleFormData.emoji}
                        onChange={(e) => setVehicleFormData({...vehicleFormData, emoji: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Multiplicador
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.1"
                        value={vehicleFormData.base_multiplier}
                        onChange={(e) => setVehicleFormData({...vehicleFormData, base_multiplier: parseFloat(e.target.value) || 1})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Capacidad
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="20"
                        value={vehicleFormData.capacity_passengers}
                        onChange={(e) => setVehicleFormData({...vehicleFormData, capacity_passengers: parseInt(e.target.value) || 1})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Nivel Requerido
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={vehicleFormData.unlock_level}
                        onChange={(e) => setVehicleFormData({...vehicleFormData, unlock_level: parseInt(e.target.value) || 1})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={vehicleFormData.is_premium}
                        onChange={(e) => setVehicleFormData({...vehicleFormData, is_premium: e.target.checked})}
                        className="mr-2"
                      />
                      <span className="text-sm font-medium text-gray-700">Vehículo Premium</span>
                    </label>
                  </div>
                </div>
                
                <div className="flex space-x-2 mt-6">
                  <button
                    onClick={() => setShowVehicleModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleSaveVehicle}
                    className="flex-1 px-4 py-2 bg-indigo-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-indigo-700"
                  >
                    {editingVehicle ? 'Actualizar' : 'Crear'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Zone Modal */}
        {showZoneModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-10 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white max-h-screen overflow-y-auto">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  {editingZone ? 'Editar Zona' : 'Crear Nueva Zona'}
                </h3>
                <form onSubmit={handleSaveZone} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ID de Zona (Grid-Pad)
                    </label>
                    <input
                      type="text"
                      value={zoneFormData.zone_name}
                      onChange={(e) => setZoneFormData({...zoneFormData, zone_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="ej: B2-5 (Grid B2, Pad 5)"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nombre para Mostrar
                    </label>
                    <input
                      type="text"
                      value={zoneFormData.display_name}
                      onChange={(e) => setZoneFormData({...zoneFormData, display_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="ej: Zona PVP Central"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo de Zona
                    </label>
                    <select
                      value={zoneFormData.zone_type}
                      onChange={(e) => setZoneFormData({...zoneFormData, zone_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="safe_zone">Zona Segura</option>
                      <option value="combat_zone">Zona de Combate</option>
                      <option value="neutral">Zona Neutral</option>
                      <option value="no_taxi">Sin Taxi</option>
                    </select>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Multiplicador Peligro
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.1"
                        value={zoneFormData.danger_multiplier}
                        onChange={(e) => setZoneFormData({...zoneFormData, danger_multiplier: parseFloat(e.target.value) || 1})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Nivel Mínimo
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={zoneFormData.min_driver_level}
                        onChange={(e) => setZoneFormData({...zoneFormData, min_driver_level: parseInt(e.target.value) || 1})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Vehículos Permitidos
                    </label>
                    <input
                      type="text"
                      value={zoneFormData.allowed_vehicles}
                      onChange={(e) => setZoneFormData({...zoneFormData, allowed_vehicles: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="auto,moto,avion"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Mensaje de Advertencia
                    </label>
                    <textarea
                      value={zoneFormData.warning_message}
                      onChange={(e) => setZoneFormData({...zoneFormData, warning_message: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      rows={2}
                      placeholder="Advertencia para los conductores..."
                    />
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="requires_confirmation"
                      checked={zoneFormData.requires_confirmation}
                      onChange={(e) => setZoneFormData({...zoneFormData, requires_confirmation: e.target.checked})}
                      className="mr-2"
                    />
                    <label htmlFor="requires_confirmation" className="text-sm font-medium text-gray-700">
                      Requiere Confirmación
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="zone_active"
                      checked={zoneFormData.is_active}
                      onChange={(e) => setZoneFormData({...zoneFormData, is_active: e.target.checked})}
                      className="mr-2"
                    />
                    <label htmlFor="zone_active" className="text-sm font-medium text-gray-700">
                      Zona Activa
                    </label>
                  </div>
                  
                  <div className="flex space-x-2 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowZoneModal(false)}
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      {editingZone ? 'Actualizar' : 'Crear'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Stop Modal */}
        {showStopModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-10 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white max-h-screen overflow-y-auto">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  {editingStop ? 'Editar Parada' : 'Crear Nueva Parada'}
                </h3>
                <form onSubmit={handleSaveStop} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ID de Parada (Grid-Pad)
                    </label>
                    <input
                      type="text"
                      value={stopFormData.stop_name}
                      onChange={(e) => setStopFormData({...stopFormData, stop_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="ej: B2-7"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nombre para Mostrar
                    </label>
                    <input
                      type="text"
                      value={stopFormData.display_name}
                      onChange={(e) => setStopFormData({...stopFormData, display_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="ej: Parada Ciudad Central"
                      required
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Emoji
                      </label>
                      <input
                        type="text"
                        value={stopFormData.emoji}
                        onChange={(e) => setStopFormData({...stopFormData, emoji: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tipo de Parada
                      </label>
                      <select
                        value={stopFormData.landmark_type}
                        onChange={(e) => setStopFormData({...stopFormData, landmark_type: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="town_stop">Parada Ciudad</option>
                        <option value="main_stop">Parada Principal</option>
                        <option value="airport_stop">Parada Aeropuerto</option>
                        <option value="seaport">Puerto</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Coord X
                      </label>
                      <input
                        type="number"
                        value={stopFormData.coordinate_x}
                        onChange={(e) => setStopFormData({...stopFormData, coordinate_x: parseFloat(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Coord Y
                      </label>
                      <input
                        type="number"
                        value={stopFormData.coordinate_y}
                        onChange={(e) => setStopFormData({...stopFormData, coordinate_y: parseFloat(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Coord Z
                      </label>
                      <input
                        type="number"
                        value={stopFormData.coordinate_z}
                        onChange={(e) => setStopFormData({...stopFormData, coordinate_z: parseFloat(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Bonus Popularidad
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.1"
                        value={stopFormData.popularity_bonus}
                        onChange={(e) => setStopFormData({...stopFormData, popularity_bonus: parseFloat(e.target.value) || 1})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Área de Espera
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={stopFormData.waiting_area_size}
                        onChange={(e) => setStopFormData({...stopFormData, waiting_area_size: parseInt(e.target.value) || 5})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="pickup_point"
                        checked={stopFormData.is_pickup_point}
                        onChange={(e) => setStopFormData({...stopFormData, is_pickup_point: e.target.checked})}
                        className="mr-2"
                      />
                      <label htmlFor="pickup_point" className="text-sm font-medium text-gray-700">
                        Punto de Recogida
                      </label>
                    </div>
                    
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="dropoff_point"
                        checked={stopFormData.is_dropoff_point}
                        onChange={(e) => setStopFormData({...stopFormData, is_dropoff_point: e.target.checked})}
                        className="mr-2"
                      />
                      <label htmlFor="dropoff_point" className="text-sm font-medium text-gray-700">
                        Punto de Destino
                      </label>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="stop_active"
                      checked={stopFormData.is_active}
                      onChange={(e) => setStopFormData({...stopFormData, is_active: e.target.checked})}
                      className="mr-2"
                    />
                    <label htmlFor="stop_active" className="text-sm font-medium text-gray-700">
                      Parada Activa
                    </label>
                  </div>
                  
                  <div className="flex space-x-2 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowStopModal(false)}
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 px-4 py-2 bg-green-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      {editingStop ? 'Actualizar' : 'Crear'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};