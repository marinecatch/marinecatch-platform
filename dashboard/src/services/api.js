// src/services/api.js
// Central API service — all calls to MarineCatch backend go through here

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'https://api.marinecatchafrica.com';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

// Auto-attach token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('mc_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-handle 401
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('mc_token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ── AUTH ──────────────────────────────────────────────────────────
export const login = (email, password) =>
  api.post('/api/v1/users/login', { email, password });

export const getMe = () =>
  api.get('/api/v1/users/me');

// ── INVENTORY ─────────────────────────────────────────────────────
export const getInventory = (params = {}) =>
  api.get('/api/v1/inventory/', { params });

export const getLot = (id) =>
  api.get(`/api/v1/inventory/${id}`);

export const getQuote = (id, quantity_kg) =>
  api.get(`/api/v1/inventory/${id}/quote`, { params: { quantity_kg } });

export const createLot = (params) =>
  api.post('/api/v1/inventory/', null, { params });

export const updateLot = (id, data) =>
  api.patch(`/api/v1/inventory/${id}`, data);

export const getMyLots = () =>
  api.get('/api/v1/inventory/my-lots/list');

// ── ORDERS ────────────────────────────────────────────────────────
export const getOrders = (params = {}) =>
  api.get('/api/v1/orders/', { params });

export const getMyOrders = () =>
  api.get('/api/v1/orders/my');

export const placeOrder = (data) =>
  api.post('/api/v1/orders/', data);

export const updateOrderStatus = (id, status) =>
  api.patch(`/api/v1/orders/${id}/status`, { status });

// ── ANALYTICS ─────────────────────────────────────────────────────
export const getPlatformSummary = () =>
  api.get('/api/v1/analytics/platform-summary');

export const getSpeciesSummary = (params = {}) =>
  api.get('/api/v1/analytics/species-summary', { params });

export const getMonthlyTrends = (params = {}) =>
  api.get('/api/v1/analytics/monthly-trends', { params });

export const getPriceIntelligence = () =>
  api.get('/api/v1/analytics/price-intelligence');

// ── USERS ─────────────────────────────────────────────────────────
export const getUsers = () =>
  api.get('/api/v1/users/');

// ── PAYMENTS ──────────────────────────────────────────────────────
export const getOrderPayment = (orderId) =>
  api.get(`/api/v1/payments/order/${orderId}`);

export default api;