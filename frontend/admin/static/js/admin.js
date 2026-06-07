// MarineCatch Africa Admin Panel — Shared Utilities

const API = window.location.origin;
// ── AUTH ──────────────────────────────────────
function getToken() {
    return localStorage.getItem('mc_admin_token');
}

function setToken(token) {
    localStorage.setItem('mc_admin_token', token);
}

function clearToken() {
    localStorage.removeItem('mc_admin_token');
    localStorage.removeItem('mc_admin_user');
    window.location.href = '/admin/login.html';
}

function getUser() {
    const u = localStorage.getItem('mc_admin_user');
    return u ? JSON.parse(u) : null;
}

function requireAuth() {
    if (!getToken()) {
        window.location.href = '/admin/login.html';
        return false;
    }
    return true;
}

// ── API CALLS ─────────────────────────────────
async function apiGet(path) {
    const res = await fetch(`${API}${path}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    if (res.status === 401) { clearToken(); return null; }
    return res.json();
}

async function apiPost(path, data) {
    const res = await fetch(`${API}${path}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    if (res.status === 401) { clearToken(); return null; }
    return res.json();
}

async function apiPatch(path, data) {
    const res = await fetch(`${API}${path}`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    if (res.status === 401) { clearToken(); return null; }
    return res.json();
}

// ── BADGE HELPERS ─────────────────────────────
function statusBadge(status) {
    const map = {
        'pending_payment': ['warning', 'Pending Payment'],
        'confirmed':       ['info',    'Confirmed'],
        'preparing':       ['info',    'Preparing'],
        'dispatched':      ['info',    'Dispatched'],
        'delivered':       ['success', 'Delivered'],
        'completed':       ['success', 'Completed'],
        'cancelled':       ['danger',  'Cancelled'],
        'paid':            ['success', 'Paid'],
        'pending':         ['warning', 'Pending'],
        'processing':      ['info',    'Processing'],
        'failed':          ['danger',  'Failed'],
        'expired':         ['danger',  'Expired'],
        'active':          ['success', 'Active'],
        'coming_soon':     ['warning', 'Coming Soon'],
        'not_served':      ['neutral', 'Not Served'],
        'low':             ['success', 'Low Risk'],
        'medium':          ['warning', 'Medium Risk'],
        'high':            ['danger',  'High Risk'],
        'breach':          ['danger',  'BREACH'],
        'warning':         ['warning', 'Warning'],
        'intact':          ['success', 'Intact'],
        'unknown':         ['neutral', 'Unknown'],
    };
    const [type, label] = map[status] || ['neutral', status];
    return `<span class="badge badge-${type}">${label}</span>`;
}

function formatKES(amount) {
    if (!amount) return 'KES 0';
    return `KES ${Number(amount).toLocaleString('en-KE', {minimumFractionDigits: 0})}`;
}

function formatDate(dt) {
    if (!dt) return '—';
    return new Date(dt).toLocaleDateString('en-KE', {
        day: '2-digit', month: 'short', year: 'numeric'
    });
}

function formatDateTime(dt) {
    if (!dt) return '—';
    return new Date(dt).toLocaleString('en-KE', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

// ── SIDEBAR ACTIVE STATE ──────────────────────
function setActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('href') === path) {
            item.classList.add('active');
        }
    });
}

// ── SHOW USER IN TOPBAR ───────────────────────
function showUser() {
    const user = getUser();
    const el = document.getElementById('admin-name');
    if (el && user) el.textContent = user.name || 'Admin';
}

// ── LOADING HELPER ────────────────────────────
function showLoading(id) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            Loading...
        </div>`;
}

function showError(id, msg) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = `<div class="alert alert-danger">${msg}</div>`;
}