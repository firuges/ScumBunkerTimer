/**
 * Main Zustand store - Authentication and Global State
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserProfile, UserPermissions, AuthAPI } from '../api/auth';
import { apiClient } from '../api/client';

interface AuthState {
  // State
  user: UserProfile | null;
  permissions: UserPermissions | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (code: string, state?: string) => Promise<void>;
  logout: (logoutAllDevices?: boolean) => Promise<void>;
  loadUser: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  
  // Helper methods
  hasPermission: (permission: string) => boolean;
  canAccessModule: (module: string) => boolean;
  hasGuildAccess: (guildId: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      permissions: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (code: string, state?: string) => {
        try {
          set({ isLoading: true, error: null });
          
          const response = await AuthAPI.login({ code, state });
          const permissions = await AuthAPI.getUserPermissions();
          
          set({
            user: response.user,
            permissions,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            user: null,
            permissions: null,
            isAuthenticated: false,
            isLoading: false,
            error: error.message || 'Login failed',
          });
          throw error;
        }
      },

      logout: async (logoutAllDevices = false) => {
        try {
          const token = apiClient.getToken();
          if (token) {
            await AuthAPI.logout(token, logoutAllDevices);
          }
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          // Clear state regardless of API call success
          set({
            user: null,
            permissions: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      loadUser: async () => {
        try {
          // Check if we have a token
          const token = apiClient.getToken();
          if (!token) {
            set({ isAuthenticated: false });
            return;
          }

          set({ isLoading: true, error: null });
          
          const user = await AuthAPI.getCurrentUser();
          const permissions = await AuthAPI.getUserPermissions();
          
          set({
            user,
            permissions,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          // Token might be expired or invalid
          apiClient.clearToken();
          set({
            user: null,
            permissions: null,
            isAuthenticated: false,
            isLoading: false,
            error: error.message || 'Failed to load user',
          });
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      // Helper methods
      hasPermission: (permission: string) => {
        const { permissions } = get();
        return permissions ? AuthAPI.hasPermission(permissions, permission) : false;
      },

      canAccessModule: (module: string) => {
        const { permissions } = get();
        return permissions ? AuthAPI.canAccessModule(permissions, module) : false;
      },

      hasGuildAccess: (guildId: string) => {
        const { user } = get();
        return user ? AuthAPI.hasGuildAccess(user, guildId) : false;
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        // Only persist user and isAuthenticated
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// UI State Store
interface UIState {
  // Sidebar
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  
  // Notifications
  notifications: Notification[];
  
  // Loading states
  globalLoading: boolean;
  
  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebarCollapse: () => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  setGlobalLoading: (loading: boolean) => void;
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: number;
  persistent?: boolean;
}

export const useUIStore = create<UIState>((set, get) => ({
  // Initial state
  sidebarOpen: true,
  sidebarCollapsed: false,
  notifications: [],
  globalLoading: false,

  // Actions
  toggleSidebar: () => {
    set((state) => ({ sidebarOpen: !state.sidebarOpen }));
  },

  setSidebarOpen: (open: boolean) => {
    set({ sidebarOpen: open });
  },

  toggleSidebarCollapse: () => {
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
  },

  addNotification: (notification) => {
    const newNotification: Notification = {
      ...notification,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: Date.now(),
    };

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Auto-remove non-persistent notifications after 5 seconds
    if (!notification.persistent) {
      setTimeout(() => {
        get().removeNotification(newNotification.id);
      }, 5000);
    }
  },

  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  clearNotifications: () => {
    set({ notifications: [] });
  },

  setGlobalLoading: (loading: boolean) => {
    set({ globalLoading: loading });
  },
}));

// Export commonly used hooks
export const useAuth = () => {
  const store = useAuthStore();
  return {
    user: store.user,
    permissions: store.permissions,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
    login: store.login,
    logout: store.logout,
    loadUser: store.loadUser,
    clearError: store.clearError,
    hasPermission: store.hasPermission,
    canAccessModule: store.canAccessModule,
    hasGuildAccess: store.hasGuildAccess,
  };
};

export const useUI = () => {
  const store = useUIStore();
  return {
    sidebarOpen: store.sidebarOpen,
    sidebarCollapsed: store.sidebarCollapsed,
    notifications: store.notifications,
    globalLoading: store.globalLoading,
    toggleSidebar: store.toggleSidebar,
    setSidebarOpen: store.setSidebarOpen,
    toggleSidebarCollapse: store.toggleSidebarCollapse,
    addNotification: store.addNotification,
    removeNotification: store.removeNotification,
    clearNotifications: store.clearNotifications,
    setGlobalLoading: store.setGlobalLoading,
  };
};