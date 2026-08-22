// MarineCatch Africa Admin Panel — Shared Utilities

const API = window.location.origin;
// ── AUTH ──────────────────────────────────────
function getToken() {
    return localStorage.getItem('mc_admin_token');
}

function setToken(token) {
    localStorage.setItem('mc_admin_token', token);
}

function toggleSidebar() {
    document.querySelector('.sidebar')?.classList.toggle('open');
    document.querySelector('.sidebar-overlay')?.classList.toggle('open');
}

function clearToken() {
    localStorage.removeItem('mc_admin_token');
    localStorage.removeItem('mc_admin_user');
    window.location.href = '/admin/pages/login.html';
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

// ── PROFILE / ACCOUNT (shared across all admin pages) ─────────────
function openProfileModal() {
    const user = getUser() || {};
    document.getElementById('pm-name').value     = user.name || '';
    document.getElementById('pm-email').value    = user.email || '';
    document.getElementById('pm-phone').value    = user.phone || '';
    document.getElementById('pm-location').value = user.location || '';
    document.getElementById('pm-age').value      = user.age || '';
    ['pm-info-error','pm-info-success','pm-password-error','pm-password-success','pm-danger-error'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    showProfileTab('info');
    document.getElementById('profile-modal').style.display = 'flex';
}

function closeProfileModal() {
    document.getElementById('profile-modal').style.display = 'none';
}

function showProfileTab(tab) {
    document.querySelectorAll('#profile-modal .tab').forEach(t => t.classList.remove('active'));
    document.getElementById(`pm-tab-${tab}`).classList.add('active');
    document.getElementById('pm-panel-info').style.display     = tab === 'info'     ? 'block' : 'none';
    document.getElementById('pm-panel-password').style.display = tab === 'password' ? 'block' : 'none';
    document.getElementById('pm-panel-danger').style.display   = tab === 'danger'   ? 'block' : 'none';
}

async function saveProfile() {
    const errEl = document.getElementById('pm-info-error');
    const sucEl = document.getElementById('pm-info-success');
    errEl.style.display = 'none';
    sucEl.style.display = 'none';

    try {
        const res = await fetch('/api/v1/users/me', {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}`},
            body: JSON.stringify({
                name: document.getElementById('pm-name').value,
                phone: document.getElementById('pm-phone').value,
                location: document.getElementById('pm-location').value,
                age: document.getElementById('pm-age').value ? parseInt(document.getElementById('pm-age').value) : null,
            })
        });
        const data = await res.json();
        if (res.ok) {
            const user = getUser() || {};
            const updated = { ...user, ...data };
            localStorage.setItem('mc_admin_user', JSON.stringify(updated));
            document.getElementById('admin-name').textContent = updated.name;
            sucEl.textContent = '✅ Profile updated';
            sucEl.style.display = 'block';
        } else {
            errEl.textContent = data.detail || 'Failed to update profile';
            errEl.style.display = 'block';
        }
    } catch(e) {
        errEl.textContent = 'Network error. Please try again.';
        errEl.style.display = 'block';
    }
}

async function changePassword() {
    const errEl = document.getElementById('pm-password-error');
    const sucEl = document.getElementById('pm-password-success');
    errEl.style.display = 'none';
    sucEl.style.display = 'none';

    const current = document.getElementById('pm-current-password').value;
    const newPass = document.getElementById('pm-new-password').value;
    const confirmPass = document.getElementById('pm-confirm-password').value;

    if (!current || !newPass) { errEl.textContent = 'Please fill in both password fields'; errEl.style.display = 'block'; return; }
    if (newPass !== confirmPass) { errEl.textContent = 'New passwords do not match'; errEl.style.display = 'block'; return; }

    try {
        const res = await fetch('/api/v1/users/me/change-password', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}`},
            body: JSON.stringify({ current_password: current, new_password: newPass })
        });
        const data = await res.json();
        if (res.ok) {
            sucEl.textContent = '✅ Password updated';
            sucEl.style.display = 'block';
            document.getElementById('pm-current-password').value = '';
            document.getElementById('pm-new-password').value = '';
            document.getElementById('pm-confirm-password').value = '';
        } else {
            errEl.textContent = data.detail || 'Failed to update password';
            errEl.style.display = 'block';
        }
    } catch(e) {
        errEl.textContent = 'Network error. Please try again.';
        errEl.style.display = 'block';
    }
}

async function deactivateAccount() {
    const errEl = document.getElementById('pm-danger-error');
    errEl.style.display = 'none';
    const pass = document.getElementById('pm-deactivate-password').value;
    if (!pass) { errEl.textContent = 'Please confirm your password'; errEl.style.display = 'block'; return; }
    if (!confirm('Are you sure you want to deactivate your own admin account? You will be logged out immediately and need another admin to reactivate you.')) return;

    try {
        const res = await fetch('/api/v1/users/me/deactivate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}`},
            body: JSON.stringify({ password: pass })
        });
        const data = await res.json();
        if (res.ok) {
            alert('Your account has been deactivated.');
            clearToken();
        } else {
            errEl.textContent = data.detail || 'Failed to deactivate account';
            errEl.style.display = 'block';
        }
    } catch(e) {
        errEl.textContent = 'Network error. Please try again.';
        errEl.style.display = 'block';
    }
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