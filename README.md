# # 91 VRS Cafe – Full-Stack System  `v2.0`

A complete **full-stack** cafe management system built by a senior developer with:

- **Backend**: Python / Django 6 + Django REST Framework + drf-spectacular
- **Frontend**: Vanilla JS, HTML5, CSS3 (PWA-ready)

---

## Repository Structure

```
cafe-system-architecture/
│
├── backend/                   ← Django REST API (senior-grade architecture)
│   ├── manage.py
│   ├── requirements.txt
│   ├── README.md              ← Detailed backend docs + full API reference
│   ├── cafe_backend/          ← Django project settings & routing
│   └── cafe/                  ← Main app
│       ├── models.py          ← 11 domain models (BaseModel mixin, indexes)
│       ├── serializers.py     ← Full serializer coverage
│       ├── views.py           ← 9 ViewSets with @extend_schema docs
│       ├── urls.py            ← Router + custom URL patterns
│       ├── admin.py           ← Professional Django admin
│       ├── filters.py         ← FilterSets (django-filter)
│       ├── exceptions.py      ← Custom business exceptions
│       ├── utils.py           ← Bill calc, QR URL, greeting helpers
│       ├── signals.py         ← Business logic signal handlers
│       └── tests.py           ← 79 passing tests
│
├── frontend/                  ← API-connected frontend
│   ├── index.html             ← Welcome / portal selection
│   ├── customer.html          ← Customer ordering page (async API)
│   ├── kitchen.html           ← Kitchen display system (KDS, async polling)
│   ├── admin.html             ← Manager dashboard (async CRUD)
│   ├── data.js                ← Full API layer v2.0 (30+ DataStore methods)
│   └── styles.css
│
├── index.html                 ← Original frontend files (unchanged)
├── customer.html
├── kitchen.html
├── admin.html
├── data.js
└── styles.css
```

---

## Quick Start

### 1. Start the Django backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_menu    # loads 27 menu items + settings
python manage.py seed_tables  # creates 12 tables
python manage.py createsuperuser
python manage.py runserver
```

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/api/` | REST API root |
| `http://127.0.0.1:8000/api/docs/` | ✨ Swagger UI |
| `http://127.0.0.1:8000/api/redoc/` | ReDoc |
| `http://127.0.0.1:8000/admin/` | Django admin |

### 2. Open the frontend

Open `frontend/index.html` in a browser. By default `data.js` targets `http://127.0.0.1:8000`.

To override the backend URL:
```html
<script>window.VRS_API_BASE = 'https://your-api.example.com';</script>
<script src="data.js"></script>
```

---

## Key Features

| Portal | Description |
|--------|-------------|
| **Customer** | Browse & search menu, filter veg/non-veg, cart, discount codes, order tracking |
| **Kitchen (KDS)** | Priority queue, real-time status, bulk actions, stock management |
| **Admin/Manager** | Floor map, reservations, reports, analytics, menu editor, settings |

## Backend Highlights

- **11 domain models** with `BaseModel` (created_at / updated_at / is_active)
- **4 new v2 models**: Table, Reservation, Discount, OrderFeedback
- **79 automated tests** (100% pass rate)
- **Swagger/OpenAPI** interactive documentation
- **django-filter** with full FilterSet support on all list endpoints
- **Pagination**, **Search**, **Ordering** on all list views
- **Custom exceptions**: TableOccupied, InvalidDiscount, ReservationConflict, MenuItemOutOfStock
- **Signals**: auto-estimated kitchen time, table status management
- **Professional Django Admin** with custom actions, fieldsets, and inlines

See `backend/README.md` for the full API reference.


A complete **full-stack** cafe management system built with:

- **Backend**: Python / Django + Django REST Framework  
- **Frontend**: Vanilla JS, HTML5, CSS3 (PWA-ready)

---

## Repository Structure

```
cafe-system-architecture/
├── backend/          ← Django REST API
│   ├── manage.py
│   ├── requirements.txt
│   ├── README.md     ← Detailed backend docs
│   ├── cafe_backend/ ← Django project settings
│   └── cafe/         ← Main app (models, views, serializers, tests)
│
├── frontend/         ← API-connected frontend (copies of original files)
│   ├── index.html    ← Welcome / portal selection
│   ├── customer.html ← Customer ordering page
│   ├── kitchen.html  ← Kitchen display system (KDS)
│   ├── admin.html    ← Manager dashboard
│   ├── data.js       ← API layer (replaces localStorage)
│   └── styles.css    ← Shared design system
│
├── index.html        ← Original frontend files (unchanged)
├── customer.html
├── kitchen.html
├── admin.html
├── data.js
└── styles.css
```

## Quick Start

### 1. Start the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_menu    # loads default menu items
python manage.py createsuperuser
python manage.py runserver
```

Backend runs at **http://127.0.0.1:8000/api/**

### 2. Open the frontend

Open `frontend/index.html` in a browser. The `data.js` file points to `http://127.0.0.1:8000` by default.

To use a different backend URL, set `window.VRS_API_BASE` before loading `data.js`:

```html
<script>window.VRS_API_BASE = 'https://your-backend.example.com';</script>
<script src="data.js"></script>
```

### 3. Django Admin

Visit **http://127.0.0.1:8000/admin/** to manage all data directly.

---

## Features

| Portal | Description |
|--------|-------------|
| **Customer** | Browse menu, add to cart, place order, track status |
| **Kitchen (KDS)** | Real-time order queue, mark pending → preparing → done |
| **Admin / Manager** | Floor map, stats, reports, menu editor, settings |

---

## API Endpoints

See `backend/README.md` for the full API reference.
