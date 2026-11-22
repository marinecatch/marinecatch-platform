// src/services/api.js — Fisher portal API service
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'https://api.marinecatchafrica.com';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('mc_fisher_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('mc_fisher_token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ── AUTH ──────────────────────────────────────────────────────────
export const login = (email, password) =>
  api.post('/api/v1/users/login', { email, password });

export const register = (data) =>
  api.post('/api/v1/users/register', data);

export const getMe = () =>
  api.get('/api/v1/users/me');

export const updateMe = (data) =>
  api.patch('/api/v1/users/me', data);

export const changePassword = (data) =>
  api.post('/api/v1/users/me/change-password', data);

export const deactivateMe = () =>
  api.post('/api/v1/users/me/deactivate');

// ── MY CATCH (inventory lots) ──────────────────────────────────────
export const getMyLots = (includeSold = false) =>
  api.get('/api/v1/inventory/my-lots/list', { params: { include_sold: includeSold } });

export const createLot = (params) =>
  api.post('/api/v1/inventory/', null, { params });

export const lotAction = (lotId, data) =>
  api.post(`/api/v1/inventory/${lotId}/action`, data);

// ── PAYOUTS ───────────────────────────────────────────────────────
export const getFisherPayouts = (fisherId) =>
  api.get(`/api/v1/payouts/fisher/${fisherId}`);

// ── COMPLIANCE & REPUTATION ────────────────────────────────────────
export const getMyComplianceProfile = (userId) =>
  api.get(`/api/v1/compliance/profiles/${userId}`);

export const getMyInspections = () =>
  api.get('/api/v1/compliance/inspections/mine');

export const getMyCluster = () =>
  api.get('/api/v1/compliance/cluster/mine');

// ── MARKET PRICES ─────────────────────────────────────────────────
export const getPriceIntelligence = () =>
  api.get('/api/v1/analytics/price-intelligence');

export default api;
