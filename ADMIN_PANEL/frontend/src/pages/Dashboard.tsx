import React from 'react';
import { 
  ChartBarIcon, 
  UsersIcon, 
  TrophyIcon,
  CurrencyDollarIcon 
} from '@heroicons/react/24/outline';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  trend?: string;
  trendColor?: 'green' | 'red' | 'gray';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, trend, trendColor = 'gray' }) => {
  const trendColors = {
    green: 'text-green-600 bg-green-100',
    red: 'text-red-600 bg-red-100',
    gray: 'text-gray-600 bg-gray-100'
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon className="h-8 w-8 text-indigo-600" />
        </div>
        <div className="ml-5 w-0 flex-1">
          <dl>
            <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
            <dd className="flex items-baseline">
              <div className="text-2xl font-semibold text-gray-900">{value}</div>
              {trend && (
                <div className={`ml-2 flex items-baseline text-sm font-semibold ${trendColors[trendColor]} px-2.5 py-0.5 rounded-full`}>
                  {trend}
                </div>
              )}
            </dd>
          </dl>
        </div>
      </div>
    </div>
  );
};

export const Dashboard: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="py-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
        
        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <StatCard
            title="Fame Points Claims"
            value="1,247"
            icon={TrophyIcon}
            trend="+12%"
            trendColor="green"
          />
          <StatCard
            title="Active Users"
            value="892"
            icon={UsersIcon}
            trend="+5.2%"
            trendColor="green"
          />
          <StatCard
            title="Taxi Rides"
            value="3,521"
            icon={ChartBarIcon}
            trend="+18%"
            trendColor="green"
          />
          <StatCard
            title="Bank Transactions"
            value="$125,430"
            icon={CurrencyDollarIcon}
            trend="-2.1%"
            trendColor="red"
          />
        </div>

        {/* Recent Activity */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Activity
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-3 border-b border-gray-200">
                <div className="flex items-center">
                  <TrophyIcon className="h-5 w-5 text-yellow-500 mr-3" />
                  <span className="text-sm text-gray-900">User claimed 500 Fame Points reward</span>
                </div>
                <span className="text-xs text-gray-500">5 min ago</span>
              </div>
              <div className="flex items-center justify-between py-3 border-b border-gray-200">
                <div className="flex items-center">
                  <ChartBarIcon className="h-5 w-5 text-blue-500 mr-3" />
                  <span className="text-sm text-gray-900">New taxi ride: Airport to City Center</span>
                </div>
                <span className="text-xs text-gray-500">12 min ago</span>
              </div>
              <div className="flex items-center justify-between py-3">
                <div className="flex items-center">
                  <CurrencyDollarIcon className="h-5 w-5 text-green-500 mr-3" />
                  <span className="text-sm text-gray-900">Bank transaction: $1,500 transfer</span>
                </div>
                <span className="text-xs text-gray-500">25 min ago</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};