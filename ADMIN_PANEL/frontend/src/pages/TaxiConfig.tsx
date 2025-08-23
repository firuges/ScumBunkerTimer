import React, { useState } from 'react';
import { TruckIcon, CogIcon, MapIcon, CalculatorIcon } from '@heroicons/react/24/outline';

export const TaxiConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState('vehicles');

  const tabs = [
    { id: 'vehicles', name: 'Vehículos', icon: TruckIcon },
    { id: 'zones', name: 'Zonas & Mapas', icon: MapIcon },
    { id: 'pricing', name: 'Precios & Tarifas', icon: CogIcon },
    { id: 'simulator', name: 'Simulador', icon: CalculatorIcon },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Configuración del Sistema Taxi</h1>
          <p className="mt-2 text-sm text-gray-600">
            Configura vehículos, zonas, precios y simula costos del sistema taxi
          </p>
        </div>

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
          {activeTab === 'vehicles' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Gestión de Vehículos</h2>
              <p className="text-gray-600 mb-6">Configura los tipos de vehículos disponibles y sus multiplicadores</p>
              
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900">Sedan</h3>
                  <p className="text-sm text-gray-500 mb-2">Vehículo estándar</p>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Multiplicador: 1.0x</span>
                    <button className="text-indigo-600 hover:text-indigo-800 text-sm">Editar</button>
                  </div>
                </div>
                
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900">SUV</h3>
                  <p className="text-sm text-gray-500 mb-2">Mayor capacidad</p>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Multiplicador: 1.5x</span>
                    <button className="text-indigo-600 hover:text-indigo-800 text-sm">Editar</button>
                  </div>
                </div>
                
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900">Helicopter</h3>
                  <p className="text-sm text-gray-500 mb-2">Transporte aéreo</p>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Multiplicador: 3.0x</span>
                    <button className="text-indigo-600 hover:text-indigo-800 text-sm">Editar</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'zones' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Zonas y Mapas</h2>
              <p className="text-gray-600 mb-6">Define zonas PVP/PVE y restricciones de transporte</p>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Zonas Configuradas</h3>
                  <div className="space-y-3">
                    <div className="border border-gray-200 rounded-lg p-3">
                      <div className="flex justify-between items-center">
                        <div>
                          <span className="font-medium">Ciudad Central</span>
                          <div className="text-sm text-gray-500">PVE Zone</div>
                        </div>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Segura
                        </span>
                      </div>
                    </div>
                    
                    <div className="border border-gray-200 rounded-lg p-3">
                      <div className="flex justify-between items-center">
                        <div>
                          <span className="font-medium">Zona Industrial</span>
                          <div className="text-sm text-gray-500">PVP Zone</div>
                        </div>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Peligrosa
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Vista del Mapa</h3>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg h-64 flex items-center justify-center">
                    <div className="text-center">
                      <MapIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-500">Editor visual de mapa próximamente</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'pricing' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Configuración de Precios</h2>
              <p className="text-gray-600 mb-6">Establece tarifas base, por kilómetro y comisiones</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tarifa Base
                    </label>
                    <input
                      type="number"
                      defaultValue="50"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Costo inicial por viaje</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tarifa por Kilómetro
                    </label>
                    <input
                      type="number"
                      defaultValue="15"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Costo por cada kilómetro</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Comisión del Sistema (%)
                    </label>
                    <input
                      type="number"
                      defaultValue="10"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Porcentaje que se queda el sistema</p>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Ejemplo de Cálculo</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Tarifa base:</span>
                      <span>$50</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Distancia (5 km):</span>
                      <span>$75</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Subtotal:</span>
                      <span>$125</span>
                    </div>
                    <div className="flex justify-between text-red-600">
                      <span>Comisión (10%):</span>
                      <span>-$12.5</span>
                    </div>
                    <div className="flex justify-between font-semibold border-t pt-2">
                      <span>Total conductor:</span>
                      <span>$112.5</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'simulator' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Simulador de Costos</h2>
              <p className="text-gray-600 mb-6">Calcula costos de viajes en tiempo real</p>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo de Vehículo
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
                      <option>Sedan (1.0x)</option>
                      <option>SUV (1.5x)</option>
                      <option>Helicopter (3.0x)</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Distancia (km)
                    </label>
                    <input
                      type="number"
                      placeholder="Ej: 10"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Zona
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
                      <option>Ciudad Central (PVE)</option>
                      <option>Zona Industrial (PVP +50%)</option>
                    </select>
                  </div>
                  
                  <button className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    Calcular Costo
                  </button>
                </div>
                
                <div className="bg-indigo-50 rounded-lg p-6">
                  <h3 className="font-semibold text-indigo-900 mb-4">Resultado del Cálculo</h3>
                  <div className="space-y-3">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-indigo-600 mb-1">$247.5</div>
                      <div className="text-sm text-indigo-700">Costo Total del Viaje</div>
                    </div>
                    
                    <div className="border-t border-indigo-200 pt-3 space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Tarifa base:</span>
                        <span>$50.00</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Distancia (10 km):</span>
                        <span>$150.00</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Multiplicador SUV:</span>
                        <span>×1.5</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Recargo PVP:</span>
                        <span>+50%</span>
                      </div>
                      <div className="flex justify-between font-medium pt-2 border-t border-indigo-200">
                        <span>Para el conductor:</span>
                        <span>$222.75</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};