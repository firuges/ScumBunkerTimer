/**
 * Super Admin Panel - Control global del ecosystem bot
 * Exclusivo para el dueño del bot con gestión cross-server
 */

import React, { useState, useEffect } from 'react';
import {
  superAdminAPI,
  GlobalDashboard,
  ServerManagement,
  SubscriptionManagement,
  DiscordServerInfo,
  SubscriptionUpdate,
  ServerActionBulk,
} from '../api/superadmin';

const SuperAdminPanel: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<string>('dashboard');

  const [globalDashboard, setGlobalDashboard] = useState<GlobalDashboard | null>(null);
  const [serverManagement, setServerManagement] = useState<ServerManagement | null>(null);
  const [subscriptionManagement, setSubscriptionManagement] = useState<SubscriptionManagement | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    setError('');
    try {
      const [dashboardData, serversData, subscriptionsData] = await Promise.all([
        superAdminAPI.getDashboard(),
        superAdminAPI.getAllServers(),
        superAdminAPI.getSubscriptionManagement()
      ]);
      
      setGlobalDashboard(dashboardData);
      setServerManagement(serversData);
      setSubscriptionManagement(subscriptionsData);
    } catch (err) {
      setError(`Error loading super admin data: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'active': return 'text-green-600 bg-green-100';
      case 'warning':
      case 'trial': return 'text-yellow-600 bg-yellow-100';
      case 'error':
      case 'suspended': return 'text-red-600 bg-red-100';
      case 'inactive': return 'text-gray-600 bg-gray-100';
      default: return 'text-blue-600 bg-blue-100';
    }
  };

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case 'free': return 'text-gray-600 bg-gray-100';
      case 'premium': return 'text-blue-600 bg-blue-100';
      case 'vip': return 'text-purple-600 bg-purple-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const renderTabButton = (tabId: string, label: string, icon: string) => (
    <button
      onClick={() => setActiveTab(tabId)}
      className={`flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors ${
        activeTab === tabId
          ? 'bg-red-100 text-red-700 border-red-300'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
      }`}
    >
      <span className="mr-2">{icon}</span>
      {label}
    </button>
  );

  const handleSubscriptionUpdate = async (guildId: string, newPlan: 'free' | 'premium' | 'vip') => {
    try {
      const update: SubscriptionUpdate = {
        guild_id: guildId,
        new_plan: newPlan,
        duration_months: 1,
        reason: `Manual update to ${newPlan} by super admin`
      };
      
      await superAdminAPI.updateServerSubscription(guildId, update);
      await loadInitialData(); // Refresh data
    } catch (err) {
      setError(`Error updating subscription: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Loading Super Admin Panel...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-6">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-sm text-red-600">⚠️ {error}</div>
            <button 
              onClick={loadInitialData}
              className="mt-2 bg-red-100 text-red-700 px-3 py-1 rounded text-sm hover:bg-red-200"
            >
              Retry
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
          <h1 className="text-3xl font-bold text-red-900">👑 Super Admin Panel</h1>
          <p className="mt-2 text-sm text-gray-600">Control global del ecosystem bot SCUM - Solo para el dueño</p>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-6">
          <div className="flex space-x-2">
            {renderTabButton('dashboard', 'Global Dashboard', '📊')}
            {renderTabButton('servers', 'Servers Management', '🌐')}
            {renderTabButton('subscriptions', 'Subscriptions', '💎')}
            {renderTabButton('system', 'System Health', '⚡')}
          </div>
        </div>

        {/* Global Dashboard Tab */}
        {activeTab === 'dashboard' && globalDashboard && (
          <div className="space-y-6">
            {/* Key Global Metrics */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <div className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="text-3xl mr-4">🌐</div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Total Servers</h3>
                    <p className="text-2xl font-bold text-gray-900">{globalDashboard.analytics.total_servers}</p>
                    <p className="text-sm text-gray-600">{globalDashboard.analytics.active_servers} active</p>
                  </div>
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="text-3xl mr-4">👥</div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Total Users</h3>
                    <p className="text-2xl font-bold text-gray-900">{formatNumber(globalDashboard.analytics.total_users)}</p>
                    <p className="text-sm text-gray-600">{formatNumber(globalDashboard.analytics.daily_active_users)} daily active</p>
                  </div>
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="text-3xl mr-4">💰</div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Monthly Revenue</h3>
                    <p className="text-2xl font-bold text-gray-900">{formatCurrency(globalDashboard.analytics.monthly_revenue)}</p>
                    <p className="text-sm text-gray-600">{globalDashboard.analytics.premium_servers + globalDashboard.analytics.vip_servers} paid servers</p>
                  </div>
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="text-3xl mr-4">⚡</div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">System Health</h3>
                    <p className="text-2xl font-bold text-gray-900">{globalDashboard.analytics.system_health.overall_uptime.toFixed(1)}%</p>
                    <p className="text-sm text-gray-600">{globalDashboard.analytics.system_health.api_response_time.toFixed(1)}ms avg</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Growth Metrics */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">📈 Growth Metrics</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="border border-gray-100 rounded p-4">
                  <h4 className="font-medium text-gray-900">New Servers</h4>
                  <div className="space-y-2 text-sm mt-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Today:</span>
                      <span className="font-medium text-green-600">+{globalDashboard.analytics.growth_metrics.new_servers_today}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Week:</span>
                      <span className="font-medium text-blue-600">+{globalDashboard.analytics.growth_metrics.new_servers_week}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Month:</span>
                      <span className="font-medium text-purple-600">+{globalDashboard.analytics.growth_metrics.new_servers_month}</span>
                    </div>
                  </div>
                </div>

                <div className="border border-gray-100 rounded p-4">
                  <h4 className="font-medium text-gray-900">Churn Rate</h4>
                  <div className="mt-2">
                    <p className="text-2xl font-bold text-red-600">{globalDashboard.analytics.growth_metrics.churned_servers_month}</p>
                    <p className="text-sm text-gray-600">servers lost this month</p>
                  </div>
                </div>

                <div className="border border-gray-100 rounded p-4">
                  <h4 className="font-medium text-gray-900">Premium Adoption</h4>
                  <div className="mt-2">
                    <p className="text-2xl font-bold text-blue-600">{((globalDashboard.analytics.premium_servers / globalDashboard.analytics.total_servers) * 100).toFixed(1)}%</p>
                    <p className="text-sm text-gray-600">servers on premium</p>
                  </div>
                </div>

                <div className="border border-gray-100 rounded p-4">
                  <h4 className="font-medium text-gray-900">Error Rate</h4>
                  <div className="mt-2">
                    <p className="text-2xl font-bold text-green-600">{globalDashboard.analytics.system_health.error_rate}%</p>
                    <p className="text-sm text-gray-600">system reliability</p>
                  </div>
                </div>
              </div>
            </div>

            {/* System Alerts */}
            {globalDashboard.alerts.length > 0 && (
              <div className="border border-yellow-200 rounded-lg p-6 bg-yellow-50">
                <h2 className="text-lg font-medium text-yellow-800 mb-4">🚨 System Alerts</h2>
                <div className="space-y-2">
                  {globalDashboard.alerts.map((alert, index) => (
                    <div key={index} className="text-sm text-yellow-700 bg-yellow-100 p-2 rounded">
                      {alert}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Servers */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">🏆 Top Performing Servers</h2>
              <div className="space-y-4">
                {globalDashboard.top_servers.slice(0, 5).map((server) => (
                  <div key={server.guild_id} className="flex justify-between items-center border-b border-gray-100 pb-2">
                    <div>
                      <h4 className="font-medium text-gray-900">{server.guild_name}</h4>
                      <p className="text-sm text-gray-600">
                        {server.commands_used_today} commands today • {server.active_users_today} active users
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-green-600">{formatCurrency(server.revenue_generated)}</p>
                      <p className="text-sm text-gray-500">monthly</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Servers Management Tab */}
        {activeTab === 'servers' && serverManagement && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-medium text-gray-900">🌐 Discord Servers Management</h2>
              <div className="text-sm text-gray-600">
                Total: {serverManagement.total_count} servers
              </div>
            </div>

            {/* Subscription Summary */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-900">Free Servers</h3>
                  <span className="text-lg font-bold text-gray-600">{serverManagement.subscription_summary.free}</span>
                </div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-900">Premium Servers</h3>
                  <span className="text-lg font-bold text-blue-600">{serverManagement.subscription_summary.premium}</span>
                </div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-900">VIP Servers</h3>
                  <span className="text-lg font-bold text-purple-600">{serverManagement.subscription_summary.vip}</span>
                </div>
              </div>
            </div>

            {/* Servers List */}
            <div className="space-y-4">
              {serverManagement.servers.map((server) => (
                <div key={server.guild_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="text-lg font-medium text-gray-900">{server.guild_name}</h3>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(server.status)}`}>
                          {server.status}
                        </span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPlanColor(server.subscription_plan)}`}>
                          {server.subscription_plan.toUpperCase()}
                        </span>
                      </div>
                      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3 text-sm text-gray-600">
                        <div>Guild ID: {server.guild_id}</div>
                        <div>Members: {formatNumber(server.member_count)}</div>
                        <div>Owner: {server.owner_username}</div>
                      </div>
                      <div className="mt-2 text-sm text-gray-600">
                        <div>Features: {server.features_enabled.join(', ')}</div>
                        <div className="mt-1">
                          Usage: {formatNumber(server.monthly_usage.commands)} commands/month • {formatNumber(server.monthly_usage.active_users)} active users
                        </div>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleSubscriptionUpdate(server.guild_id, 'premium')}
                        disabled={server.subscription_plan === 'premium'}
                        className={`px-3 py-1 rounded text-sm ${
                          server.subscription_plan === 'premium' 
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                        }`}
                      >
                        → Premium
                      </button>
                      <button
                        onClick={() => handleSubscriptionUpdate(server.guild_id, 'vip')}
                        disabled={server.subscription_plan === 'vip'}
                        className={`px-3 py-1 rounded text-sm ${
                          server.subscription_plan === 'vip' 
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                        }`}
                      >
                        → VIP
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Subscriptions Tab */}
        {activeTab === 'subscriptions' && subscriptionManagement && (
          <div className="space-y-6">
            <h2 className="text-xl font-medium text-gray-900">💎 Subscription Management</h2>
            
            {/* Revenue Summary */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <div className="border border-gray-200 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-900">Monthly Recurring</h3>
                <p className="text-2xl font-bold text-green-600">{formatCurrency(subscriptionManagement.revenue_summary.monthly_recurring)}</p>
              </div>
              <div className="border border-gray-200 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-900">This Month</h3>
                <p className="text-2xl font-bold text-blue-600">{formatCurrency(subscriptionManagement.revenue_summary.total_this_month)}</p>
              </div>
              <div className="border border-gray-200 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-900">Last Month</h3>
                <p className="text-2xl font-bold text-gray-600">{formatCurrency(subscriptionManagement.revenue_summary.total_last_month)}</p>
              </div>
              <div className="border border-gray-200 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-900">Annual Projection</h3>
                <p className="text-2xl font-bold text-purple-600">{formatCurrency(subscriptionManagement.revenue_summary.annual_projection)}</p>
              </div>
            </div>

            {/* Active Subscriptions */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Active Subscriptions</h3>
              <div className="space-y-4">
                {subscriptionManagement.active_subscriptions.map((subscription) => (
                  <div key={subscription.id} className="border border-gray-100 rounded p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-gray-900">Server {subscription.guild_id.slice(-4)}</span>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPlanColor(subscription.plan)}`}>
                            {subscription.plan.toUpperCase()}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                          Started: {new Date(subscription.start_date).toLocaleDateString()} • 
                          Expires: {subscription.end_date ? new Date(subscription.end_date).toLocaleDateString() : 'Never'}
                        </div>
                        {subscription.reason && (
                          <div className="text-xs text-gray-500 mt-1">Reason: {subscription.reason}</div>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">{subscription.status}</div>
                        <div className="text-xs text-gray-500">by {subscription.upgraded_by}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* System Health Tab */}
        {activeTab === 'system' && globalDashboard && (
          <div className="space-y-6">
            <h2 className="text-xl font-medium text-gray-900">⚡ System Health Monitor</h2>
            
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {globalDashboard.system_health.map((health) => (
                <div key={health.service_name} className="border border-gray-200 rounded-lg p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-medium text-gray-900">{health.service_name}</h3>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(health.status)}`}>
                      {health.status === 'healthy' ? '✅ Healthy' : 
                       health.status === 'warning' ? '⚠️ Warning' : '❌ Error'}
                    </span>
                  </div>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex justify-between">
                      <span>Response Time:</span>
                      <span className="font-medium">{health.response_time.toFixed(1)}ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Uptime:</span>
                      <span className="font-medium">{health.uptime_percentage.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Errors:</span>
                      <span className="font-medium">{health.error_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Last Check:</span>
                      <span className="font-medium">{new Date(health.last_check).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Recent Admin Actions */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Admin Actions</h3>
              <div className="space-y-4">
                {globalDashboard.recent_actions.map((action) => (
                  <div key={action.id} className="border border-gray-100 rounded p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {action.action_type}
                          </span>
                          <span className="text-sm font-medium text-gray-900">by {action.admin_username}</span>
                        </div>
                        <div className="text-sm text-gray-600">
                          Target: {action.target_guild_id ? `Server ${action.target_guild_id.slice(-4)}` : 'Global'}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Details: {JSON.stringify(action.details)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-gray-500">{new Date(action.timestamp).toLocaleString()}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SuperAdminPanel;