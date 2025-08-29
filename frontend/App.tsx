
import React from 'react';
import { useAuth } from './context/AuthContext';
import AuthPage from './components/auth/AuthPage';
import Dashboard from './components/dashboard/Dashboard';

const App: React.FC = () => {
  const { accessToken } = useAuth();

  return (
    <div className="min-h-screen bg-dark">
      {accessToken ? <Dashboard /> : <AuthPage />}
    </div>
  );
};

export default App;
