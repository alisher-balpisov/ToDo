
import React, { createContext, useState, useContext, useEffect, ReactNode, useCallback } from 'react';
import apiService, { tokenManager } from '../services/apiService';
import { UserRegisterSchema, UserLoginSchema, UserPasswordUpdateSchema } from '../components/auth/types';

interface AuthContextType {
  accessToken: string | null;
  login: (credentials: UserLoginSchema) => Promise<void>;
  register: (userData: UserRegisterSchema) => Promise<any>;
  logout: () => void;
  changePassword: (data: UserPasswordUpdateSchema) => Promise<any>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [accessToken, setAccessToken] = useState<string | null>(tokenManager.getAccessToken());

  useEffect(() => {
    const token = tokenManager.getAccessToken();
    if (token) {
      setAccessToken(token);
    }
  }, []);

  const login = useCallback(async (credentials: UserLoginSchema) => {
    const params = new URLSearchParams();
    params.append('username', credentials.username);
    params.append('password', credentials.password);
    
    const data = await fetch( 'http://localhost:8000/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params,
    }).then(res => {
        if (!res.ok) throw new Error("Login failed");
        return res.json();
    });

    tokenManager.setTokens(data.access_token, data.refresh_token);
    setAccessToken(data.access_token);
  }, []);

  const register = async (userData: UserRegisterSchema) => {
    return apiService<any>('/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  };
  
  const changePassword = async (data: UserPasswordUpdateSchema) => {
     return apiService<any>('/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  const logout = useCallback(() => {
    tokenManager.clearTokens();
    setAccessToken(null);
  }, []);

  return (
    <AuthContext.Provider value={{ accessToken, login, register, logout, changePassword }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
