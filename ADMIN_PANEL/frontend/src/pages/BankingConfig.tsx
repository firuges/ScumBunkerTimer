import React, { useState } from 'react';
import { BanknotesIcon, CogIcon, ChartBarIcon, ClockIcon } from '@heroicons/react/24/outline';

export const BankingConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState('general');

  const tabs = [
    { id: 'general', name: 'Configuración General', icon: CogIcon },
    { id: 'interest', name: 'Tasas de Interés', icon: BanknotesIcon },
    { id: 'transactions', name: 'Transacciones', icon: ChartBarIcon },
    { id: 'schedules', name: 'Horarios', icon: ClockIcon },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Sistema Bancario</h1>
          <p className="mt-2 text-sm text-gray-600">
            Configura balances iniciales, tasas de interés y límites de transacciones
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
          {activeTab === 'general' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Configuración General</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Balance Inicial de Bienvenida
                    </label>
                    <input
                      type="number"
                      defaultValue="1000"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Dinero que reciben los nuevos usuarios</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Límite de Transacción Máxima
                    </label>
                    <input
                      type="number"
                      defaultValue="50000"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Máximo dinero por transacción</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Comisión por Transferencia (%)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      defaultValue="2.5"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Porcentaje de comisión por transferir dinero</p>
                  </div>
                  
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        defaultChecked
                        className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200"
                      />
                      <span className="ml-2 text-sm text-gray-700">Permitir transacciones entre usuarios</span>
                    </label>
                  </div>
                  
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        defaultChecked
                        className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200"
                      />
                      <span className="ml-2 text-sm text-gray-700">Registro de todas las transacciones</span>
                    </label>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Estadísticas Actuales</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total en circulación:</span>
                      <span className="text-sm font-semibold">$2,847,390</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Usuarios activos:</span>
                      <span className="text-sm font-semibold">1,234</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Transacciones hoy:</span>
                      <span className="text-sm font-semibold">456</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Comisiones generadas:</span>
                      <span className="text-sm font-semibold">$12,847</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'interest' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Tasas de Interés</h2>
              <p className="text-gray-600 mb-6">Configura intereses por mantener dinero en el banco</p>
              
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-2">Interés Diario</h3>
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        step="0.01"
                        defaultValue="0.5"
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                      <span className="text-sm text-gray-500">%</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Interés aplicado cada 24 horas</p>
                  </div>
                  
                  <div className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-2">Interés Semanal</h3>
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        step="0.01"
                        defaultValue="3.0"
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                      <span className="text-sm text-gray-500">%</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Bonus adicional semanal</p>
                  </div>
                  
                  <div className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-2">Balance Mínimo</h3>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">$</span>
                      <input
                        type="number"
                        defaultValue="100"
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Mínimo para generar intereses</p>
                  </div>
                </div>
                
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-900 mb-2">Calculadora de Intereses</h3>
                  <p className="text-sm text-blue-700 mb-3">
                    Con $10,000 en el banco:
                  </p>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="font-semibold text-blue-900">Diario</div>
                      <div className="text-blue-700">+$50.00</div>
                    </div>
                    <div>
                      <div className="font-semibold text-blue-900">Semanal</div>
                      <div className="text-blue-700">+$300.00</div>
                    </div>
                    <div>
                      <div className="font-semibold text-blue-900">Mensual</div>
                      <div className="text-blue-700">+$1,500.00</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'transactions' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Historial de Transacciones</h2>
              
              <div className="mb-4">
                <div className="flex space-x-4">
                  <input
                    type="text"
                    placeholder="Buscar por usuario..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <select className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <option>Todas las transacciones</option>
                    <option>Solo transferencias</option>
                    <option>Solo depósitos</option>
                    <option>Solo retiros</option>
                  </select>
                </div>
              </div>
              
              <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                <table className="min-w-full divide-y divide-gray-300">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Usuario</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Tipo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Cantidad</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Fecha</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Usuario#1234</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Transferencia</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">$1,500</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Hace 5 min</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Completada
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Usuario#5678</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Depósito</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">$2,000</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Hace 12 min</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Completada
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Usuario#9012</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Retiro</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">$750</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Hace 1 hora</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Pendiente
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'schedules' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Horarios de Operación</h2>
              <p className="text-gray-600 mb-6">Configura los horarios donde el banco está disponible</p>
              
              <div className="space-y-4">
                <div>
                  <label className="flex items-center mb-4">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200"
                    />
                    <span className="ml-2 text-sm font-medium text-gray-700">Banco disponible 24/7</span>
                  </label>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 opacity-50">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Horarios por Día</h3>
                    <div className="space-y-2">
                      {['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'].map((day) => (
                        <div key={day} className="flex items-center justify-between py-2 border-b border-gray-200">
                          <span className="text-sm text-gray-600">{day}</span>
                          <div className="flex items-center space-x-2">
                            <input
                              type="time"
                              defaultValue="09:00"
                              className="text-xs border border-gray-300 rounded px-2 py-1"
                              disabled
                            />
                            <span className="text-xs text-gray-400">a</span>
                            <input
                              type="time"
                              defaultValue="18:00"
                              className="text-xs border border-gray-300 rounded px-2 py-1"
                              disabled
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Configuraciones Especiales</h3>
                    <div className="space-y-3">
                      <div>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            className="rounded border-gray-300 text-indigo-600 shadow-sm"
                            disabled
                          />
                          <span className="ml-2 text-sm text-gray-500">Cerrado en feriados</span>
                        </label>
                      </div>
                      
                      <div>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            className="rounded border-gray-300 text-indigo-600 shadow-sm"
                            disabled
                          />
                          <span className="ml-2 text-sm text-gray-500">Horario reducido fines de semana</span>
                        </label>
                      </div>
                      
                      <div>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            defaultChecked
                            className="rounded border-gray-300 text-indigo-600 shadow-sm"
                            disabled
                          />
                          <span className="ml-2 text-sm text-gray-500">Intereses se calculan fuera de horario</span>
                        </label>
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