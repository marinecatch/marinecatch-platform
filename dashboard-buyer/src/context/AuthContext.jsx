// src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, getMe } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('mc_buyer_token');
    if (token) {
      getMe()
        .then(res => setUser(res.data))
        .catch(() => localStorage.removeItem('mc_buyer_token'))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const res = await apiLogin(email, password);
    if (res.data.user.role !== 'buyer') {
      throw new Error('This portal is for buyers only.');
    }
    localStorage.setItem('mc_buyer_token', res.data.access_token);
    setUser(res.data.user);
    return res.data.user;
  };

  const logout = () => {
    localStorage.removeItem('mc_buyer_token');
    localStorage.removeItem('mc_buyer_cart');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
