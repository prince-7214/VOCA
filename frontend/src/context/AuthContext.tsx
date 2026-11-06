import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { User, LoginCredentials, RegisterCredentials } from '../types';
import { loginUser, registerUser, getCurrentUser } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('voca_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('voca_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Validate token on mount
  useEffect(() => {
    async function verifyAuth() {
      const storedToken = localStorage.getItem('voca_token');
      if (storedToken) {
        try {
          const profile = await getCurrentUser();
          setUser(profile);
          localStorage.setItem('voca_user', JSON.stringify(profile));
        } catch {
          // Token expired or invalid
          logout();
        }
      }
      setIsLoading(false);
    }
    verifyAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const res = await loginUser(credentials);
    setToken(res.access_token);
    setUser(res.user);
    localStorage.setItem('voca_token', res.access_token);
    localStorage.setItem('voca_user', JSON.stringify(res.user));
  };

  const register = async (credentials: RegisterCredentials) => {
    const res = await registerUser(credentials);
    setToken(res.access_token);
    setUser(res.user);
    localStorage.setItem('voca_token', res.access_token);
    localStorage.setItem('voca_user', JSON.stringify(res.user));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('voca_token');
    localStorage.removeItem('voca_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
