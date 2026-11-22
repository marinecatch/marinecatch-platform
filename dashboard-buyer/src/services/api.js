// src/services/api.js — Buyer portal API service
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'https://api.marinecatchafrica.com';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('mc_buyer_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('mc_buyer_token');
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

// ── MARKETPLACE (browse available lots) ────────────────────────────
export const browseInventory = (params = {}) =>
  api.get('/api/v1/inventory/', { params });

export const getLotDetail = (lotId) =>
  api.get(`/api/v1/inventory/${lotId}`);

export const getLotQuote = (lotId, quantityKg) =>
  api.get(`/api/v1/inventory/${lotId}/quote`, { params: { quantity_kg: quantityKg } });

export const reserveLot = (lotId, quantityKg) =>
  api.post(`/api/v1/inventory/${lotId}/reserve`, null, { params: { quantity_kg: quantityKg } });

export const releaseLot = (lotId) =>
  api.post(`/api/v1/inventory/${lotId}/release`);

// ── CART CHECKOUT ─────────────────────────────────────────────────
export const checkoutCart = (data) =>
  api.post('/api/v1/orders/checkout-cart', data);

// ── ORDERS ────────────────────────────────────────────────────────
export const getMyOrders = (params = {}) =>
  api.get('/api/v1/orders/me', { params });

export const getOrder = (orderId) =>
  api.get(`/api/v1/orders/${orderId}`);

export const trackOrder = (orderId) =>
  api.get(`/api/v1/orders/track/${orderId}`);

export const cancelOrder = (orderId) =>
  api.post(`/api/v1/orders/${orderId}/cancel`);

export const confirmOrder = (orderId) =>
  api.post(`/api/v1/orders/${orderId}/confirm`);

// ── PAYMENTS ──────────────────────────────────────────────────────
export const getOrderPayment = (orderId) =>
  api.get(`/api/v1/payments/order/${orderId}`);

export const initiatePayment = (data) =>
  api.post('/api/v1/payments/initiate', data);

// ── LPO REQUESTS ──────────────────────────────────────────────────
// Note: there's no "my LPO requests" endpoint yet — buyers can submit
// a request and see the immediate result, but history/status of past
// requests isn't queryable from this role. Fulfilled items appear as
// normal orders in getMyOrders() once admin assigns a lot.
export const submitLpoRequest = (data) =>
  api.post('/api/v1/lpo/requests', data);

// ── MARKET INTELLIGENCE ───────────────────────────────────────────
export const getPriceIntelligence = () =>
  api.get('/api/v1/analytics/price-intelligence');

export default api;
