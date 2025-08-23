import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import LoginPage from './components/auth/LoginPage';
import { Dashboard } from './pages/Dashboard';
import { FameRewards } from './pages/FameRewards';
import { TaxiConfig } from './pages/TaxiConfig';
import { BankingConfig } from './pages/BankingConfig';
import { useAuthStore } from './store/authStore';
import NotificationContainer from './components/ui/NotificationContainer';
import './App.css';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/*" element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/fame-rewards" element={<FameRewards />} />
                  <Route path="/taxi-config" element={<TaxiConfig />} />
                  <Route path="/banking" element={<BankingConfig />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          } />
        </Routes>
        <NotificationContainer />
      </div>
    </Router>
  );
}

export default App;
