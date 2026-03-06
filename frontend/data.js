// ============================================
// # 91 VRS CAFE - API DATA LAYER
// Connects to Django REST Framework backend
// ============================================

// Change this to your backend URL in production
const API_BASE = (window.VRS_API_BASE || 'http://127.0.0.1:8000') + '/api';

// ---- low-level fetch helpers ----

async function apiGet(path) {
    const resp = await fetch(API_BASE + path);
    if (!resp.ok) throw new Error(`GET ${path} → ${resp.status}`);
    return resp.json();
}

async function apiPost(path, body = {}) {
    const resp = await fetch(API_BASE + path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `POST ${path} → ${resp.status}`);
    }
    return resp.json();
}

async function apiPatch(path, body = {}) {
    const resp = await fetch(API_BASE + path, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `PATCH ${path} → ${resp.status}`);
    }
    return resp.json();
}

async function apiDelete(path) {
    const resp = await fetch(API_BASE + path, { method: 'DELETE' });
    if (!resp.ok) throw new Error(`DELETE ${path} → ${resp.status}`);
}

// ---- Category data (static) ----

const categories = [
    { id: 'all', name: 'All', emoji: '✨' },
    { id: 'trending', name: 'Trending', emoji: '🔥' },
    { id: 'coffee', name: 'Coffee', emoji: '☕' },
    { id: 'burgers', name: 'Burgers', emoji: '🍔' },
    { id: 'pizza', name: 'Pizza', emoji: '🍕' },
    { id: 'mains', name: 'Mains', emoji: '🍛' },
    { id: 'desserts', name: 'Desserts', emoji: '🍰' },
    { id: 'drinks', name: 'Drinks', emoji: '🍹' },
    { id: 'snacks', name: 'Snacks', emoji: '🍟' },
];

// ---- API DataStore ----

const DataStore = {

    // ---- Menu ----

    async getMenuItems(category = null) {
        const qs = category && category !== 'all' ? `?category=${category}` : '';
        return apiGet(`/menu/${qs}`);
    },

    async addMenuItem(item) {
        return apiPost('/menu/', item);
    },

    async updateMenuItem(id, updates) {
        const resp = await fetch(`${API_BASE}/menu/${id}/`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
        });
        if (!resp.ok) throw new Error(`PATCH /menu/${id}/ → ${resp.status}`);
        return resp.json();
    },

    async deleteMenuItem(id) {
        return apiDelete(`/menu/${id}/`);
    },

    async toggleStock(id) {
        return apiPost(`/menu/${id}/toggle_stock/`);
    },

    // ---- Sessions ----

    async getSessions() {
        return apiGet('/sessions/');
    },

    async getSession(tableNum) {
        try {
            return await apiGet(`/sessions/${tableNum}/`);
        } catch {
            return null;
        }
    },

    async createSession(tableNum, items, customerName = '', specialInstructions = '') {
        return apiPost(`/sessions/${tableNum}/`, {
            customer_name: customerName,
            special_instructions: specialInstructions,
            items: items.map(i => ({ id: i.id, qty: i.qty })),
        });
    },

    async closeSession(tableNum) {
        return apiPost(`/sessions/${tableNum}/close/`);
    },

    async markBillPrinted(tableNum) {
        return apiPost(`/sessions/${tableNum}/mark_bill_printed/`);
    },

    // ---- Kitchen Orders ----

    async getKitchenOrders(statusFilter = null) {
        const qs = statusFilter ? `?status=${statusFilter}` : '';
        return apiGet(`/kitchen/${qs}`);
    },

    async updateOrderStatus(orderId, status) {
        return apiPatch(`/kitchen/${orderId}/status/`, { status });
    },

    // ---- Sales History ----

    async getSalesHistory() {
        return apiGet('/sales/');
    },

    async getTodayStats() {
        return apiGet('/stats/');
    },

    // ---- Settings ----

    async getSettings() {
        return apiGet('/settings/');
    },

    async saveSettings(settings) {
        return apiPost('/settings/', settings);
    },
};

// ---- Theme Manager ----

const ThemeManager = {
    init() {
        const saved = localStorage.getItem('vrs_theme') || 'dark';
        this.set(saved);
    },
    get() {
        return document.documentElement.getAttribute('data-theme') || 'dark';
    },
    set(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('vrs_theme', theme);
    },
    toggle() {
        const current = this.get();
        this.set(current === 'dark' ? 'light' : 'dark');
        return this.get();
    },
};

// ---- Utility Functions ----

function showToast(message, type = 'success') {
    if (navigator.vibrate) navigator.vibrate(50);

    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span style="font-size:16px">${icons[type] || 'ℹ'}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        toast.style.transition = 'all 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createConfetti() {
    const colors = ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];
    for (let i = 0; i < 50; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.animationDelay = Math.random() * 0.5 + 's';
        confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
        document.body.appendChild(confetti);
        setTimeout(() => confetti.remove(), 3500);
    }
}

function playSound() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = 800;
        gain.gain.value = 0.2;
        osc.start();
        osc.stop(ctx.currentTime + 0.15);
    } catch (e) { /* ignore */ }
}

function formatTime(date) {
    return new Date(date).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function getElapsedMinutes(time) {
    return Math.floor((Date.now() - new Date(time).getTime()) / 60000);
}

// Initialize theme on load
document.addEventListener('DOMContentLoaded', () => ThemeManager.init());
