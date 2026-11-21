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

// ── EXECUTIVE (CEO) ───────────────────────────────────────────────
export const getExecutiveSummary = () =>
  api.get('/api/v1/analytics/executive-summary');

export const getLiquidity = () =>
  api.get('/api/v1/analytics/liquidity');

// ── COMPLIANCE ────────────────────────────────────────────────────
export const getComplianceProfiles = (params = {}) =>
  api.get('/api/v1/compliance/profiles', { params });

export const getComplianceProfile = (userId) =>
  api.get(`/api/v1/compliance/profiles/${userId}`);

export const verifyNationalId = (data) =>
  api.post('/api/v1/compliance/verify/national-id', data);

export const verifyBmu = (data) =>
  api.post('/api/v1/compliance/verify/bmu', data);

export const verifyKra = (data) =>
  api.post('/api/v1/compliance/verify/kra', data);

export const recalculateTrustScore = (userId) =>
  api.post(`/api/v1/compliance/trust-score/${userId}/recalculate`);

export const getInspections = (params = {}) =>
  api.get('/api/v1/compliance/inspections', { params });

export const getPendingInspections = () =>
  api.get('/api/v1/compliance/inspections/pending');

export const createInspection = (data) =>
  api.post('/api/v1/compliance/inspections', data);

export const getClusterLeaderboard = () =>
  api.get('/api/v1/compliance/clusters/leaderboard');

export const getDrafts = (params = {}) =>
  api.get('/api/v1/compliance/drafts', { params });

export const acceptDraft = (draftId) =>
  api.post(`/api/v1/compliance/drafts/${draftId}/accept`);

// ── INTELLIGENCE (Geography / Species) ───────────────────────────
export const getCountries = () =>
  api.get('/api/v1/intelligence/countries');

export const getAdminGeography = (params = {}) =>
  api.get('/api/v1/intelligence/admin-geography', { params });

export const getAdminGeographyTree = (params = {}) =>
  api.get('/api/v1/intelligence/admin-geography/tree', { params });

export const getLandingSites = (params = {}) =>
  api.get('/api/v1/intelligence/landing-sites', { params });

export const getLandingSite = (siteId) =>
  api.get(`/api/v1/intelligence/landing-sites/${siteId}`);

export const getBmus = (params = {}) =>
  api.get('/api/v1/intelligence/bmus', { params });

export const getMarineManagementAreas = (params = {}) =>
  api.get('/api/v1/intelligence/marine-management-areas', { params });

export const getIntelSpecies = (params = {}) =>
  api.get('/api/v1/intelligence/species', { params });

export const getIntelSpeciesDetail = (speciesId) =>
  api.get(`/api/v1/intelligence/species/${speciesId}`);

export const getDataQuality = () =>
  api.get('/api/v1/intelligence/data-quality');

export const getSources = (params = {}) =>
  api.get('/api/v1/intelligence/sources', { params });

// ── SALES & CRM ───────────────────────────────────────────────────
export const getPipelineSummary = () =>
  api.get('/api/v1/sales/pipeline-summary');

export const getLeadsByRole = () =>
  api.get('/api/v1/sales/leads-by-role');

export const getLeadSources = () =>
  api.get('/api/v1/sales/lead-sources');

export const getLeadsTimeline = (params = {}) =>
  api.get('/api/v1/sales/leads-timeline', { params });

export const getRecentLeads = (params = {}) =>
  api.get('/api/v1/sales/recent-leads', { params });

export const getSalesOverview = () =>
  api.get('/api/v1/sales/overview');

// ── LPO ───────────────────────────────────────────────────────────
export const getLpos = (params = {}) =>
  api.get('/api/v1/lpo/', { params });

export const getLpo = (reference) =>
  api.get(`/api/v1/lpo/${reference}`);

export const createLpo = (data) =>
  api.post('/api/v1/lpo/', data);

// ── NEWSLETTER ────────────────────────────────────────────────────
export const getNewsletterSubscribers = (params = {}) =>
  api.get('/api/v1/newsletter/subscribers', { params });

export const getNewsletterOverview = () =>
  api.get('/api/v1/newsletter/overview');

export const deleteNewsletterSubscriber = (id) =>
  api.delete(`/api/v1/newsletter/subscribers/${id}`);

// ── WHATSAPP INBOX ────────────────────────────────────────────────
export const getWhatsappConversations = (params = {}) =>
  api.get('/api/v1/whatsapp-log/conversations', { params });

export const getWhatsappConversation = (phoneNumber) =>
  api.get(`/api/v1/whatsapp-log/conversation/${phoneNumber}`);

export const getWhatsappOverview = () =>
  api.get('/api/v1/whatsapp-log/overview');

// ── LOGISTICS NETWORK ─────────────────────────────────────────────
export const getLogisticsNetworkSummary = () =>
  api.get('/api/v1/logistics-network/summary');

export const getLogisticsPartners = (params = {}) =>
  api.get('/api/v1/logistics-network/partners', { params });

export const getStorageNodes = (params = {}) =>
  api.get('/api/v1/logistics-network/storage-nodes', { params });

export const getCoolers = (params = {}) =>
  api.get('/api/v1/logistics-network/coolers', { params });

export const updateCoolerStatus = (coolerId, status) =>
  api.patch(`/api/v1/logistics-network/coolers/${coolerId}/status`, { status });

export const getActiveJobs = () =>
  api.get('/api/v1/logistics-network/jobs/active');

export const updateJobStatus = (jobId, status) =>
  api.patch(`/api/v1/logistics-network/jobs/${jobId}/status`, { status });

export const getOpenExceptions = () =>
  api.get('/api/v1/logistics-network/exceptions/open');

export const resolveException = (exceptionId, data) =>
  api.post(`/api/v1/logistics-network/exceptions/${exceptionId}/resolve`, data);

export const getPendingPartnerApplications = () =>
  api.get('/api/v1/logistics-network/partner-applications/pending');

export const approvePartnerApplication = (partnerId) =>
  api.post(`/api/v1/logistics-network/partner-applications/${partnerId}/approve`);

export default api;