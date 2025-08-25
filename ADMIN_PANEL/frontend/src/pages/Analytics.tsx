/**
 * Analytics Dashboard - Página principal de métricas consolidadas
 */

import React, { useState, useEffect } from 'react';
import {
  getAnalyticsDashboard,
  getSystemHealth,
  getRecentActivity,
  AnalyticsDashboard,
  SystemHealth,
  ActivityLog,
} from '../api/analytics';

const AnalyticsPage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<string>('overview');

  const [dashboard, setDashboard] = useState<AnalyticsDashboard | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth[]>([]);
  const [recentActivity, setRecentActivity] = useState<ActivityLog[]>([]);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    setLoading(true);
    setError('');
    try {
      const [dashboardData, healthData, activityData] = await Promise.all([
        getAnalyticsDashboard(),
        getSystemHealth(),
        getRecentActivity()
      ]);
      
      setDashboard(dashboardData);
      setSystemHealth(healthData);
      setRecentActivity(activityData);
    } catch (err) {
      setError(`Error loading analytics: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const renderTabButton = (tabId: string, label: string, icon: string) => (
    <button
      onClick={() => setActiveTab(tabId)}
      className={`flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors ${
        activeTab === tabId
          ? 'bg-indigo-100 text-indigo-700 border-indigo-300'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
      }`}
    >
      <span className="mr-2">{icon}</span>
      {label}
    </button>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Cargando analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-6">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-sm text-red-600">❌ {error}</div>
            <button 
              onClick={loadAnalyticsData}
              className="mt-2 bg-red-100 text-red-700 px-3 py-1 rounded text-sm hover:bg-red-200"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">📊 Analytics Dashboard</h1>
          <p className="mt-2 text-sm text-gray-600">Métricas consolidadas de todos los sistemas</p>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-6">
          <div className="flex space-x-2">
            {renderTabButton('overview', 'Resumen', '📈')}
            {renderTabButton('systems', 'Sistemas', '🔧')}
            {renderTabButton('activity', 'Actividad', '📋')}
            {renderTabButton('performance', 'Rendimiento', '⚡')}
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && dashboard && (
          <div className="space-y-6">
            {/* Key Metrics Cards */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <div className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="text-3xl mr-4">🏆</div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Fame Points</h3>
                    <p className="text-2xl font-bold text-gray-900">{dashboard.fame_metrics.total_rewards}</p>
                    <p className="text-sm text-gray-600">{formatNumber(dashboard.fame_metrics.total_points_distributed)} puntos distribuidos</p>
                  </div>
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="text-3xl mr-4">💰</div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Banking Total</h3>
                    <p className="text-2xl font-bold text-gray-900">{formatCurrency(dashboard.banking_metrics.total_balance)}</p>
                    <p className="text-sm text-gray-600">{dashboard.banking_metrics.total_accounts} cuentas activas</p>
                  </div>
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="text-3xl mr-4">🚗</div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Taxi Revenue</h3>
                    <p className="text-2xl font-bold text-gray-900">{formatCurrency(dashboard.taxi_metrics.total_revenue)}</p>
                    <p className="text-sm text-gray-600">{dashboard.taxi_metrics.total_rides_completed} viajes completados</p>
                  </div>
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="text-3xl mr-4">🔧</div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Mechanic Services</h3>
                    <p className="text-2xl font-bold text-gray-900">{dashboard.mechanic_metrics.completed_services}</p>
                    <p className="text-sm text-gray-600">{formatCurrency(dashboard.mechanic_metrics.total_revenue)} generados</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Growth Trends */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">📈 Tendencias de Crecimiento</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {Object.entries(dashboard.growth_trends).map(([system, trends]) => (
                  <div key={system} className="border border-gray-100 rounded p-4">
                    <h4 className="font-medium text-gray-900 capitalize mb-2">{system}</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Hoy:</span>
                        <span className="font-medium">+{trends.today}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Semana:</span>
                        <span className="font-medium">+{trends.week}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Mes:</span>
                        <span className="font-medium">+{trends.month}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Systems Health Tab */}
        {activeTab === 'systems' && (
          <div className="space-y-6">
            <h2 className="text-xl font-medium text-gray-900">🏥 Estado de los Sistemas</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {systemHealth.map((system) => (
                <div key={system.system_name} className="border border-gray-200 rounded-lg p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-medium text-gray-900">{system.system_name}</h3>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(system.status)}`}>
                      {system.status === 'healthy' ? '✅ Healthy' : 
                       system.status === 'warning' ? '⚠️ Warning' : '❌ Error'}
                    </span>
                  </div>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex justify-between">
                      <span>Response Time:</span>
                      <span className="font-medium">{system.response_time.toFixed(1)}ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Uptime:</span>
                      <span className="font-medium">{system.uptime_percentage.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Errors:</span>
                      <span className="font-medium">{system.error_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Last Check:</span>
                      <span className="font-medium">{new Date(system.last_check).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <div className="space-y-6">
            <h2 className="text-xl font-medium text-gray-900">📋 Actividad Reciente</h2>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 capitalize">
                          {activity.system}
                        </span>
                        <span className="text-sm font-medium text-gray-900">{activity.action}</span>
                      </div>
                      <p className="text-sm text-gray-600">{activity.details}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">{new Date(activity.timestamp).toLocaleString()}</p>
                      {activity.user_id && (
                        <p className="text-xs text-gray-400">User: {activity.user_id}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && dashboard && (
          <div className="space-y-6">
            <h2 className="text-xl font-medium text-gray-900">⚡ Rendimiento del Sistema</h2>
            
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* System Comparison */}
              <div className="border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">📊 Comparación de Sistemas</h3>
                <div className="space-y-3">
                  {Object.entries(dashboard.system_activity_comparison).map(([system, value]) => (
                    <div key={system} className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900 capitalize">{system}:</span>
                      <div className="flex items-center">
                        <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{width: `${Math.min((value / Math.max(...Object.values(dashboard.system_activity_comparison))) * 100, 100)}%`}}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600">{formatNumber(value)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Summary Stats */}
              <div className="border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">📈 Resumen General</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Sistemas Activos:</span>
                    <span className="text-lg font-bold text-green-600">{dashboard.total_systems_active}/4</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Total Registros:</span>
                    <span className="text-lg font-bold text-blue-600">{formatNumber(dashboard.total_database_records)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Última Actualización:</span>
                    <span className="text-sm text-gray-900">{new Date(dashboard.generated_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsPage;