/**
 * Sidebar Navigation Component
 */

import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import {
  HomeIcon,
  ChartBarIcon,
  CogIcon,
  TrophyIcon,
  TruckIcon,
  BanknotesIcon,
  WrenchScrewdriverIcon,
  CubeIcon,
  UsersIcon,
  DocumentTextIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  Bars3Icon,
  XMarkIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  permission?: string;
  badge?: string;
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Fame Points', href: '/fame-rewards', icon: TrophyIcon },
  { name: 'Taxi System', href: '/taxi-config', icon: TruckIcon },
  { name: 'Banking', href: '/banking', icon: BanknotesIcon },
  { name: 'Mechanics', href: '/mechanic', icon: WrenchScrewdriverIcon },
  { name: 'Bunkers', href: '/bunkers', icon: CubeIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Super Admin', href: '/superadmin', icon: ShieldCheckIcon, badge: 'OWNER' },
  { name: 'User Management', href: '/users', icon: UsersIcon },
  { name: 'Audit Logs', href: '/logs', icon: DocumentTextIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
];

const Sidebar: React.FC = () => {
  const user = useAuthStore(state => state.user);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Filter navigation items based on permissions
  const filteredNavigation = navigation.filter(item => {
    if (!item.permission) return true;
    // For now, show all items - permission system will be implemented later
    return true;
  });

  return (
    <>
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        >
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" />
        </div>
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 flex flex-col transition-all duration-300 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0 ${
        sidebarCollapsed ? 'lg:w-16' : 'lg:w-64'
      } w-64 bg-white border-r border-gray-200 shadow-sm`}>
        
        {/* Header */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          {!sidebarCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg p-2">
                <span className="text-white font-bold text-lg">🤖</span>
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">SCUM Admin</h1>
                <p className="text-xs text-gray-500">Bot Management</p>
              </div>
            </div>
          )}
          
          {/* Collapse button - desktop only */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden lg:flex items-center justify-center w-8 h-8 rounded-md hover:bg-gray-100 transition-colors"
          >
            {sidebarCollapsed ? (
              <ChevronRightIcon className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronLeftIcon className="w-5 h-5 text-gray-500" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {filteredNavigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700 border-r-2 border-indigo-600'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`
              }
              title={sidebarCollapsed ? item.name : undefined}
            >
              <item.icon
                className={`flex-shrink-0 w-5 h-5 ${
                  sidebarCollapsed ? 'mr-0' : 'mr-3'
                }`}
                aria-hidden="true"
              />
              {!sidebarCollapsed && (
                <>
                  <span className="truncate">{item.name}</span>
                  {item.badge && (
                    <span className="ml-auto bg-indigo-100 text-indigo-600 px-2 py-1 text-xs rounded-full">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        {!sidebarCollapsed && (
          <div className="border-t border-gray-200 p-4">
            <div className="text-xs text-gray-500 text-center">
              <p>SCUM Bot Admin Panel</p>
              <p className="mt-1">v1.0.0</p>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default Sidebar;