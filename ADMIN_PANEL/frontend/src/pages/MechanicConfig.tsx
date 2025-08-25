/**
 * Página de Configuración del Sistema Mecánico - Versión Simplificada
 */

import React, { useState, useEffect } from 'react';
import {
  getMechanicConfig,
  getMechanics,
  getVehiclePrices,
  getServices,
  getMechanicStats,
  MechanicConfig,
  RegisteredMechanic,
  VehiclePrice,
  MechanicService,
  MechanicStats,
} from '../api/mechanic';

const MechanicConfigPage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  const [config, setConfig] = useState<MechanicConfig | null>(null);
  const [mechanics, setMechanics] = useState<RegisteredMechanic[]>([]);
  const [vehiclePrices, setVehiclePrices] = useState<VehiclePrice[]>([]);
  const [services, setServices] = useState<MechanicService[]>([]);
  const [stats, setStats] = useState<MechanicStats | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [configData, mechanicsData, pricesData, servicesData, statsData] = await Promise.all([
        getMechanicConfig(),
        getMechanics(),
        getVehiclePrices(),
        getServices(),
        getMechanicStats()
      ]);
      
      setConfig(configData);
      setMechanics(mechanicsData);
      setVehiclePrices(pricesData);
      setServices(servicesData);
      setStats(statsData);
    } catch (err) {
      setError(`Error loading data: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Cargando configuración mecánica...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">🔧 Sistema Mecánico</h1>
          <p className="mt-2 text-sm text-gray-600">Configuración completa del módulo mecánico y seguros</p>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-sm text-red-600">❌ {error}</div>
          </div>
        )}

        <div className="bg-white shadow rounded-lg p-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {stats && (
              <>
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="text-2xl mr-3">🔧</div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Mecánicos</h3>
                      <p className="text-2xl font-bold text-gray-900">{stats.total_mechanics}</p>
                      <p className="text-sm text-gray-600">{stats.active_mechanics} activos</p>
                    </div>
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="text-2xl mr-3">📝</div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Servicios Totales</h3>
                      <p className="text-2xl font-bold text-gray-900">{stats.total_services}</p>
                      <p className="text-sm text-gray-600">{stats.completed_services} completados</p>
                    </div>
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="text-2xl mr-3">⏳</div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Servicios Pendientes</h3>
                      <p className="text-2xl font-bold text-gray-900">{stats.pending_services}</p>
                      <p className="text-sm text-gray-600">En espera</p>
                    </div>
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="text-2xl mr-3">💰</div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Ingresos Totales</h3>
                      <p className="text-2xl font-bold text-gray-900">${stats.total_revenue}</p>
                      <p className="text-sm text-gray-600">Promedio: ${stats.average_service_cost}/servicio</p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="mt-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Mecánicos Registrados ({mechanics.length})</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {mechanics.map(mechanic => (
                <div key={mechanic.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="text-sm font-medium text-gray-900">{mechanic.ingame_name}</h4>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      mechanic.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {mechanic.status === 'active' ? '✅ Activo' : '❌ Inactivo'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Experiencia:</strong> {mechanic.experience_level}</p>
                    <p><strong>Servicios:</strong> {mechanic.total_services}</p>
                    <p><strong>Rating:</strong> ⭐ {mechanic.rating}/5.0</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Precios de Vehículos ({vehiclePrices.length})</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {vehiclePrices.map(price => (
                <div key={price.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="text-sm font-medium text-gray-900">{price.vehicle_type.toUpperCase()}</h4>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      price.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {price.is_active ? '✅ Activo' : '❌ Inactivo'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Precio base:</strong> ${price.price}</p>
                    <p><strong>Multiplicador:</strong> x{price.price_multiplier}</p>
                    <p><strong>Recargo PVP:</strong> +{price.pvp_surcharge_percent}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Servicios Recientes ({services.length})</h2>
            <div className="space-y-4">
              {services.slice(0, 3).map(service => (
                <div key={service.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="text-sm font-medium text-gray-900">🆔 {service.service_id}</h4>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      service.status === 'completed' ? 'bg-green-100 text-green-800' : 
                      service.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {service.status === 'completed' ? '✅ Completado' : 
                       service.status === 'pending' ? '⏳ Pendiente' : '❌ Cancelado'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Vehículo:</strong> {service.vehicle_type} - ${service.cost}</p>
                    <p><strong>Cliente:</strong> {service.client_display_name || service.ingame_name}</p>
                    <p><strong>Creado:</strong> {new Date(service.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {config && (
            <div className="mt-8 p-4 bg-gray-50 rounded-lg">
              <h2 className="text-lg font-medium text-gray-900 mb-2">Configuración Actual</h2>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 text-sm text-gray-600">
                <p><strong>Comisión sistema:</strong> {config.commission_percent}%</p>
                <p><strong>Tarifa base:</strong> ${config.default_vehicle_insurance_rate}</p>
                <p><strong>Recargo PVP:</strong> {config.pvp_zone_surcharge_percent}%</p>
                <p><strong>Timeout servicios:</strong> {config.service_timeout_hours}h</p>
                <p><strong>Sistema activo:</strong> {config.is_active ? '✅ Sí' : '❌ No'}</p>
                <p><strong>Auto-asignación:</strong> {config.auto_assign_mechanics ? '✅ Sí' : '❌ No'}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MechanicConfigPage;