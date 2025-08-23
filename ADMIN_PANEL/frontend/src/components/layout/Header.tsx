/**
 * Header Component
 */

import React from 'react';
import { useAuth, useUI } from '../../store';
import {
  Bars3Icon,
  BellIcon,
  UserCircleIcon,
  ChevronDownIcon,
  ArrowRightOnRectangleIcon,
  CogIcon,
} from '@heroicons/react/24/outline';

const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const { toggleSidebar, notifications } = useUI();

  const handleLogout = async () => {
    if (window.confirm('Are you sure you want to logout?')) {
      await logout();
    }
  };

  const unreadNotifications = notifications.filter(n => !n.persistent).length;

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
          >
            <Bars3Icon className="w-6 h-6" />
          </button>
          
          <div className="hidden sm:block">
            <h1 className="text-xl font-semibold text-gray-900">
              Bot Administration
            </h1>
            <p className="text-sm text-gray-500">
              Manage your Discord bot configuration
            </p>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <button className="relative p-2 text-gray-400 hover:text-gray-600">
            <BellIcon className="w-6 h-6" />
            {unreadNotifications > 0 && (
              <span className="absolute top-0 right-0 block w-3 h-3 bg-danger-500 rounded-full transform translate-x-1 -translate-y-1">
                <span className="sr-only">{unreadNotifications} notifications</span>
              </span>
            )}
          </button>

          {/* User menu */}
          <div className="relative">
            <div className="flex items-center space-x-3">
              {/* User avatar */}
              <div className="flex-shrink-0">
                {user?.avatar_url ? (
                  <img
                    className="w-8 h-8 rounded-full"
                    src={user.avatar_url}
                    alt={user.username}
                  />
                ) : (
                  <UserCircleIcon className="w-8 h-8 text-gray-400" />
                )}
              </div>

              {/* User info - hidden on mobile */}
              <div className="hidden md:block">
                <p className="text-sm font-medium text-gray-900">
                  {user?.username}#{user?.discriminator}
                </p>
                <p className="text-xs text-gray-500 capitalize">
                  {user?.role?.replace('_', ' ')}
                </p>
              </div>

              {/* Dropdown trigger */}
              <ChevronDownIcon className="w-4 h-4 text-gray-400" />
            </div>

            {/* Dropdown menu - would need proper implementation with state management */}
            <div className="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5">
              <div className="py-1">
                <button className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left">
                  <CogIcon className="w-4 h-4 mr-3" />
                  Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                >
                  <ArrowRightOnRectangleIcon className="w-4 h-4 mr-3" />
                  Sign out
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;