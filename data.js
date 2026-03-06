// ============================================
// SK Cafe CAFE - DATA MANAGEMENT SYSTEM
// ============================================

// Theme Management
const ThemeManager = {
    init() {
        const saved = localStorage.getItem('sk_theme') || 'dark';
        this.set(saved);
    },

    get() {
        return document.documentElement.getAttribute('data-theme') || 'dark';
    },

    set(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('sk_theme', theme);
    },

    toggle() {
        const current = this.get();
        this.set(current === 'dark' ? 'light' : 'dark');
        return this.get();
    }
};

// Menu Data
const menuItems = [
    // Coffee
    { id: 1, name: "Caramel Macchiato", price: 220, category: "coffee", image: "https://images.unsplash.com/photo-1485808191679-5f86510681a2?w=400", emoji: "☕", isVeg: true, inStock: true, trending: true, description: "Espresso with vanilla & caramel drizzle", calories: 180 },
    { id: 2, name: "Iced Latte", price: 180, category: "coffee", image: "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400", emoji: "🧊", isVeg: true, inStock: true, trending: true, description: "Chilled espresso with creamy milk", calories: 120 },
    { id: 3, name: "Espresso Shot", price: 120, category: "coffee", image: "https://images.unsplash.com/photo-1510707577719-ae7c14805e3a?w=400", emoji: "⚡", isVeg: true, inStock: true, description: "Pure concentrated coffee", calories: 5 },
    { id: 4, name: "Mocha Frappe", price: 250, category: "coffee", image: "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400", emoji: "🍫", isVeg: true, inStock: true, description: "Blended chocolate coffee delight", calories: 290 },
    { id: 5, name: "Cappuccino", price: 180, category: "coffee", image: "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400", emoji: "☕", isVeg: true, inStock: true, description: "Classic Italian coffee with foam", calories: 140 },

    // Burgers
    { id: 6, name: "Classic Smash Burger", price: 320, category: "burgers", image: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400", emoji: "🍔", isVeg: false, inStock: true, trending: true, description: "Juicy double patty with special sauce", calories: 650 },
    { id: 7, name: "Cheese Overload", price: 380, category: "burgers", image: "https://images.unsplash.com/photo-1550547660-d9450f859349?w=400", emoji: "🧀", isVeg: false, inStock: true, description: "Triple cheese melted burger", calories: 720 },
    { id: 8, name: "Veggie Supreme", price: 280, category: "burgers", image: "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=400", emoji: "🥗", isVeg: true, inStock: true, description: "Fresh garden veggie patty", calories: 380 },
    { id: 9, name: "Chicken Zinger", price: 340, category: "burgers", image: "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400", emoji: "🍗", isVeg: false, inStock: true, trending: true, description: "Crispy spicy chicken burger", calories: 580 },

    // Pizza
    { id: 10, name: "Margherita", price: 350, category: "pizza", image: "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400", emoji: "🍕", isVeg: true, inStock: true, trending: true, description: "Classic tomato basil cheese", calories: 450 },
    { id: 11, name: "Pepperoni Feast", price: 450, category: "pizza", image: "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400", emoji: "🔥", isVeg: false, inStock: true, description: "Loaded with pepperoni slices", calories: 620 },
    { id: 12, name: "BBQ Chicken", price: 480, category: "pizza", image: "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400", emoji: "🍗", isVeg: false, inStock: true, description: "Smoky BBQ chicken pizza", calories: 580 },
    { id: 13, name: "Veggie Delight", price: 380, category: "pizza", image: "https://images.unsplash.com/photo-1511689660979-10d2b1aada49?w=400", emoji: "🥬", isVeg: true, inStock: true, description: "Garden fresh vegetables", calories: 420 },

    // Desserts
    { id: 14, name: "Molten Brownie", price: 180, category: "desserts", image: "https://images.unsplash.com/photo-1564355808539-22fda35bed7e?w=400", emoji: "🍫", isVeg: true, inStock: true, description: "Warm gooey chocolate brownie", calories: 380 },
    { id: 15, name: "NY Cheesecake", price: 280, category: "desserts", image: "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=400", emoji: "🍰", isVeg: true, inStock: true, trending: true, description: "Creamy New York style", calories: 450 },
    { id: 16, name: "Gelato Trio", price: 220, category: "desserts", image: "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=400", emoji: "🍨", isVeg: true, inStock: true, description: "Three artisan gelato scoops", calories: 320 },

    // Drinks
    { id: 17, name: "Berry Mojito", price: 180, category: "drinks", image: "https://images.unsplash.com/photo-1551538827-9c037cb4f32a?w=400", emoji: "🍹", isVeg: true, inStock: true, description: "Refreshing berry mint cooler", calories: 120 },
    { id: 18, name: "Fresh Lemonade", price: 120, category: "drinks", image: "https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=400", emoji: "🍋", isVeg: true, inStock: true, description: "Tangy homemade lemonade", calories: 90 },
    { id: 19, name: "Mango Tango", price: 160, category: "drinks", image: "https://images.unsplash.com/photo-1623065422902-30a2d299bbe4?w=400", emoji: "🥭", isVeg: true, inStock: true, trending: true, description: "Tropical mango smoothie", calories: 180 },

    // Snacks
    { id: 20, name: "French Fries", price: 120, category: "snacks", image: "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400", emoji: "🍟", isVeg: true, inStock: true, description: "Crispy golden fries", calories: 320 },
    { id: 21, name: "Loaded Nachos", price: 220, category: "snacks", image: "https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?w=400", emoji: "🌮", isVeg: true, inStock: true, trending: true, description: "Cheese salsa loaded nachos", calories: 480 },
    { id: 22, name: "Chicken Wings", price: 280, category: "snacks", image: "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=400", emoji: "🍗", isVeg: false, inStock: true, description: "Spicy buffalo wings", calories: 420 },
    { id: 23, name: "Paneer Tikka", price: 260, category: "snacks", image: "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=400", emoji: "🧀", isVeg: true, inStock: true, description: "Grilled cottage cheese", calories: 280 },

    // Mains
    { id: 24, name: "Butter Chicken", price: 380, category: "mains", image: "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=400", emoji: "🍛", isVeg: false, inStock: true, trending: true, description: "Creamy tomato chicken curry", calories: 490 },
    { id: 25, name: "Paneer Butter Masala", price: 340, category: "mains", image: "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400", emoji: "🧀", isVeg: true, inStock: true, description: "Rich paneer in butter gravy", calories: 420 },
    { id: 26, name: "Veg Biryani", price: 280, category: "mains", image: "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400", emoji: "🍚", isVeg: true, inStock: true, description: "Aromatic spiced rice", calories: 380 },
    { id: 27, name: "Chicken Biryani", price: 350, category: "mains", image: "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=400", emoji: "🍗", isVeg: false, inStock: true, trending: true, description: "Hyderabadi dum biryani", calories: 520 }
];

const categories = [
    { id: "all", name: "All", emoji: "✨" },
    { id: "trending", name: "Trending", emoji: "🔥" },
    { id: "coffee", name: "Coffee", emoji: "☕" },
    { id: "burgers", name: "Burgers", emoji: "🍔" },
    { id: "pizza", name: "Pizza", emoji: "🍕" },
    { id: "mains", name: "Mains", emoji: "🍛" },
    { id: "desserts", name: "Desserts", emoji: "🍰" },
    { id: "drinks", name: "Drinks", emoji: "🍹" },
    { id: "snacks", name: "Snacks", emoji: "🍟" }
];

// Data Store with error handling
const DataStore = {
    // Safe localStorage get with error handling
    _safeGet(key, defaultValue = null) {
        try {
            const stored = localStorage.getItem(key);
            return stored ? JSON.parse(stored) : defaultValue;
        } catch (e) {
            console.warn(`Error reading ${key} from localStorage:`, e);
            return defaultValue;
        }
    },

    // Safe localStorage set with error handling
    _safeSet(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.warn(`Error saving ${key} to localStorage:`, e);
            if (e.name === 'QuotaExceededError') {
                showToast('Storage full! Please clear some data.', 'error');
            }
            return false;
        }
    },

    getMenuItems() {
        const stored = this._safeGet('vrs_menu');
        if (stored) return stored;
        this._safeSet('vrs_menu', menuItems);
        return menuItems;
    },

    saveMenuItems(items) {
        this._safeSet('vrs_menu', items);
    },

    addMenuItem(item) {
        const items = this.getMenuItems();
        item.id = Date.now();
        item.inStock = true;
        items.push(item);
        this.saveMenuItems(items);
        return item;
    },

    updateMenuItem(id, updates) {
        const items = this.getMenuItems();
        const index = items.findIndex(i => i.id === id);
        if (index !== -1) {
            items[index] = { ...items[index], ...updates };
            this.saveMenuItems(items);
        }
        return items;
    },

    deleteMenuItem(id) {
        let items = this.getMenuItems();
        items = items.filter(i => i.id !== id);
        this.saveMenuItems(items);
        return items;
    },

    toggleStock(id) {
        const items = this.getMenuItems();
        const item = items.find(i => i.id === id);
        if (item) {
            item.inStock = !item.inStock;
            this.saveMenuItems(items);
        }
        return items;
    },

    // Session Management
    getSessions() {
        return this._safeGet('vrs_sessions', {});
    },

    saveSessions(sessions) {
        this._safeSet('vrs_sessions', sessions);
    },

    getSession(tableNum) {
        const sessions = this.getSessions();
        return sessions[tableNum] || null;
    },

    createSession(tableNum, items, customerName = '', specialInstructions = '') {
        const sessions = this.getSessions();

        if (!sessions[tableNum]) {
            sessions[tableNum] = {
                tableNum,
                items: [],
                customerName: '',
                specialInstructions: '',
                startTime: new Date().toISOString(),
                billPrinted: false
            };
        }

        if (customerName) sessions[tableNum].customerName = customerName;
        if (specialInstructions) {
            sessions[tableNum].specialInstructions += (sessions[tableNum].specialInstructions ? ' | ' : '') + specialInstructions;
        }

        items.forEach(newItem => {
            const existing = sessions[tableNum].items.find(i => i.id === newItem.id);
            if (existing) {
                existing.qty += newItem.qty;
            } else {
                sessions[tableNum].items.push({ ...newItem });
            }
        });

        this.saveSessions(sessions);
        return sessions[tableNum];
    },

    closeSession(tableNum) {
        const sessions = this.getSessions();
        const session = sessions[tableNum];

        if (session) {
            const history = this.getSalesHistory();
            const total = session.items.reduce((s, i) => s + i.price * i.qty, 0);
            history.push({
                ...session,
                closedTime: new Date().toISOString(),
                total: Math.round(total * 1.05)
            });
            this._safeSet('vrs_sales', history);
            delete sessions[tableNum];
            this.saveSessions(sessions);
        }
        return session;
    },

    markBillPrinted(tableNum) {
        const sessions = this.getSessions();
        if (sessions[tableNum]) {
            sessions[tableNum].billPrinted = true;
            this.saveSessions(sessions);
        }
    },

    // Kitchen Orders
    getKitchenOrders() {
        return this._safeGet('vrs_kitchen', []);
    },

    saveKitchenOrders(orders) {
        this._safeSet('vrs_kitchen', orders);
    },

    addKitchenOrder(tableNum, items, customerName = '', specialInstructions = '') {
        const orders = this.getKitchenOrders();
        orders.push({
            id: Date.now(),
            tableNum,
            customerName,
            specialInstructions,
            items: items.map(i => ({ ...i })),
            status: 'pending',
            time: new Date().toISOString()
        });
        this.saveKitchenOrders(orders);
    },

    updateOrderStatus(orderId, status) {
        const orders = this.getKitchenOrders();
        const order = orders.find(o => o.id === orderId);
        if (order) {
            order.status = status;
            if (status === 'completed') order.completedTime = new Date().toISOString();
            this.saveKitchenOrders(orders);
        }
        return order;
    },

    // Sales History
    getSalesHistory() {
        return this._safeGet('vrs_sales', []);
    },

    getTodayStats() {
        const today = new Date().toDateString();
        const sales = this.getSalesHistory().filter(s =>
            new Date(s.closedTime).toDateString() === today
        );
        const revenue = sales.reduce((s, o) => s + (o.total || 0), 0);
        const orders = sales.length;
        const activeTables = Object.keys(this.getSessions()).length;
        const avgOrder = orders > 0 ? Math.round(revenue / orders) : 0;

        return { revenue, orders, activeTables, avgOrder };
    },

    // Settings
    getSettings() {
        const defaultSettings = {
            cafeName: 'SK Cafe',
            phone: '+91 98765 43210',
            address: '123 Coffee Street, Bengaluru',
            gst: '29XXXXX1234X1ZX',
            taxRate: 5,
            totalTables: 12
        };
        return this._safeGet('vrs_settings', defaultSettings);
    },

    saveSettings(settings) {
        this._safeSet('vrs_settings', settings);
    },

    clearAll() {
        localStorage.removeItem('vrs_sessions');
        localStorage.removeItem('vrs_kitchen');
        localStorage.removeItem('vrs_sales');
    }
};

// Utility Functions
function showToast(message, type = 'success') {
    if (navigator.vibrate) navigator.vibrate(50);

    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span style="font-size:16px">${icons[type]}</span><span>${message}</span>`;
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
    } catch (e) { }
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
