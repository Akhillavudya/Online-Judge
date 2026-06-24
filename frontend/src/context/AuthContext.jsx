import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('verdex_token') || '');
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    async function loadUser() {
      try {
        const { data } = await api.get('/auth/me');
        setUser(data.user);
      } catch {
        localStorage.removeItem('verdex_token');
        setToken('');
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    loadUser();
  }, [token]);

  async function login(payload) {
    const { data } = await api.post('/auth/login', payload);
    localStorage.setItem('verdex_token', data.token);
    setToken(data.token);
    setUser(data.user);
    return data.user;
  }

  async function register(payload) {
    const { data } = await api.post('/auth/register', payload);
    localStorage.setItem('verdex_token', data.token);
    setToken(data.token);
    setUser(data.user);
    return data.user;
  }

  async function logout() {
    await api.post('/auth/logout').catch(() => {});
    localStorage.removeItem('verdex_token');
    setToken('');
    setUser(null);
  }

  const value = useMemo(
    () => ({ token, user, isAuthenticated: Boolean(token && user), isLoading, login, register, logout }),
    [token, user, isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider');
  return context;
}
