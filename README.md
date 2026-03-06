# # SK cafe — Full-Stack Cafe Management System  `v3.0`

A **production-ready, full-stack** Point-of-Sale and cafe management system built on **Django REST Framework** (backend) and **vanilla HTML/CSS/JS** (frontend). Designed for small-to-medium cafes with dine-in, takeaway, and delivery workflows.

---

## 📋 Table of Contents

1. [Features Overview](#features-overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Backend API Reference](#backend-api-reference)
5. [Customer Experience (IP-based, No Login)](#customer-experience)
6. [Staff Authentication](#staff-authentication)
7. [QR Code Management](#qr-code-management)
8. [Behaviour Tracking & Suggestions](#behaviour-tracking--suggestions)
9. [Database & SQL Schema](#database--sql-schema)
10. [Frontend Pages](#frontend-pages)
11. [Admin Panel](#admin-panel)
12. [Testing](#testing)
13. [Configuration](#configuration)
14. [Deployment](#deployment)

---

## Features Overview

### 🍽️ Menu Management
- Full CRUD for menu items (name, price, category, image, emoji, veg/non-veg, calories, allergens)
- 7 categories: Coffee, Burgers, Pizza, Mains, Desserts, Drinks, Snacks
- One-click **toggle stock** and **toggle trending** actions
- Filter by category, stock status, trending; full-text search
- Sort order control for custom display ordering

### 🪑 Table Management
- 12+ configurable dining tables with capacity and location info
- Status lifecycle: Available → Occupied → Reserved → Maintenance
- **QR code generation** per table (PNG stored as base64 data URI)
- **Print QR code sheets** — bulk-print all table QR codes from admin
- `GET /api/tables/{id}/qr_code/` — on-demand QR image generation via API

### 📋 Order Sessions
- Dine-in, Takeaway, and Delivery session types
- Customers add items to a session; kitchen auto-notified
- Discount code application with real-time validation
- Bill generation with subtotal / discount / tax / total breakdown
- Mark bill as printed; close session → archives to SalesRecord

### 👨‍🍳 Kitchen Display System (KDS)
- Real-time kitchen order tickets auto-created when items are ordered
- Priority levels: Normal / High / Urgent
- Status flow: Pending → Preparing → Completed
- Bulk status update endpoint
- Estimated preparation time tracking

### 📅 Reservations
- Table reservation with date, time, party size, customer phone
- Conflict detection (no double-booking same table+time)
- Status lifecycle: Pending → Confirmed → Seated → Completed / Cancelled
- Staff actions: confirm, seat, cancel via API or admin

### 💰 Discounts & Promotions
- Promo codes (percentage or fixed INR discount)
- Date range validity, min order amount, max uses cap
- `POST /api/discounts/validate/` — check code before applying

### 📊 Sales & Analytics
- Every closed session archived as a `SalesRecord` with full item snapshot
- `GET /api/stats/` — today's revenue, orders, avg order, active tables, feedback rating
- `GET /api/stats/top_items/` — top 10 best-sellers by quantity
- `GET /api/stats/hourly/` — revenue by hour for today
- `GET /api/stats/category_breakdown/` — revenue per food category
- 3 SQL database views: `v_daily_revenue`, `v_popular_items`, `v_table_status`

### ⭐ Customer Feedback
- Post-visit ratings (1–5 stars) for overall experience, food, and service
- "Would recommend" flag
- Linked to closed SalesRecord for traceability

### 👤 Customer Experience (No Login Required)
- Customers are identified **by IP address only** — no account needed
- `CustomerVisit` model stores: IP, preferred name, visit count, first/last seen
- **Behaviour tracking**: previous orders, personal top picks, trending suggestions
- **Welcome-back message**: "Welcome back, Alice! 👋" for returning customers
- `GET /api/customer/suggestions/` — Zomato-style personalised recommendation feed

### 🔐 Staff Authentication (Token-based)
- `POST /api/auth/login/` — username/password → auth token
- `POST /api/auth/logout/` — revoke token
- `GET /api/auth/me/` — current user profile + role
- `POST /api/auth/toggle_duty/` — toggle on-duty status
- 3 roles: **Admin**, **Kitchen**, **Waiter**
- Admin-only: settings, discount management
- Kitchen-or-Admin: kitchen order updates

### ⚙️ Cafe Settings (Singleton)
- Cafe name, phone, address, GST number
- Tax rate, currency symbol, UPI ID, Instagram URL
- Opening/closing times, total tables count

---

## Architecture

```
cafe-system-architecture/
├── backend/                    # Django REST Framework API
│   ├── cafe/
│   │   ├── models.py           # 13 models (BaseModel mixin)
│   │   ├── views.py            # 10 ViewSets, 40+ endpoints
│   │   ├── serializers.py      # All serializers
│   │   ├── urls.py             # URL routing
│   │   ├── admin.py            # Full Django admin
│   │   ├── permissions.py      # IsAdminStaff, IsKitchenOrAdmin, IsStaffMember
│   │   ├── filters.py          # django-filter FilterSets
│   │   ├── exceptions.py       # Custom API exceptions
│   │   ├── signals.py          # Post-save signals
│   │   ├── utils.py            # calculate_bill, QR generation, IP extraction
│   │   ├── tests.py            # 105+ tests
│   │   ├── migrations/         # 3 migrations
│   │   └── management/
│   │       └── commands/
│   │           ├── seed_menu.py       # Seed 27 menu items
│   │           ├── seed_tables.py     # Seed 12 tables
│   │           └── create_staff.py    # Create default staff accounts
│   ├── cafe_backend/
│   │   ├── settings.py         # Django settings
│   │   └── urls.py             # Root URL conf + Swagger
│   ├── schema.sql              # Full SQL DDL documentation
│   └── requirements.txt
├── frontend/                   # API-connected frontend
│   ├── index.html              # Landing/welcome page
│   ├── customer.html           # Customer ordering page
│   ├── kitchen.html            # Kitchen display system
│   ├── admin.html              # Staff management dashboard
│   ├── data.js                 # API layer (30+ async methods)
│   └── styles.css              # Shared styles
└── README.md
```

---

## Quick Start

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run migrations
```bash
python manage.py migrate
```

### 3. Seed the database
```bash
python manage.py seed_menu       # Creates 27 menu items + 12 tables
python manage.py create_staff    # Creates admin, kitchen1, waiter1 accounts
```

### 4. Start the server
```bash
python manage.py runserver
```

API available at `http://127.0.0.1:8000/api/`  
Swagger UI: `http://127.0.0.1:8000/api/docs/`  
Admin panel: `http://127.0.0.1:8000/admin/`

### 5. Open the frontend
Open `frontend/index.html` in your browser (or serve with any static file server).

---

## Backend API Reference

Base URL: `http://127.0.0.1:8000/api/`

| Resource | Endpoints |
|---|---|
| Menu | `GET/POST /menu/` · `GET/PUT/PATCH/DELETE /menu/{id}/` · `POST /menu/{id}/toggle_stock/` · `POST /menu/{id}/toggle_trending/` |
| Tables | `GET/POST /tables/` · `GET/PUT/PATCH/DELETE /tables/{id}/` · `GET /tables/{id}/session/` · `GET /tables/{id}/qr_redirect/` · `GET /tables/{id}/qr_code/` |
| Sessions | `GET /sessions/` · `GET/POST /sessions/{table_num}/` · `POST /sessions/{table_num}/close/` · `POST /sessions/{table_num}/mark_bill_printed/` · `GET /sessions/{table_num}/generate_bill/` |
| Kitchen | `GET /kitchen/` · `GET/PATCH /kitchen/{id}/` · `PATCH /kitchen/{id}/status/` · `POST /kitchen/bulk_update/` |
| Reservations | `GET/POST /reservations/` · `GET/PUT/PATCH/DELETE /reservations/{id}/` · `POST /reservations/{id}/confirm/` · `POST /reservations/{id}/seat/` · `POST /reservations/{id}/cancel/` |
| Sales | `GET /sales/` · `GET /sales/{id}/` |
| Discounts | `GET/POST /discounts/` · `GET/PUT/PATCH/DELETE /discounts/{id}/` · `POST /discounts/validate/` |
| Feedback | `GET /feedback/` · `GET /feedback/{id}/` · `POST /feedback/` |
| Stats | `GET /stats/` · `GET /stats/top_items/` · `GET /stats/hourly/` · `GET /stats/category_breakdown/` |
| Auth | `POST /auth/login/` · `POST /auth/logout/` · `GET /auth/me/` · `POST /auth/toggle_duty/` |
| Customer | `GET /customer/me/` · `GET /customer/orders/` · `POST /customer/update_name/` · `GET /customer/suggestions/` |
| Settings | `GET /settings/` · `POST /settings/` |

Full interactive documentation: **`/api/docs/`** (Swagger UI) or **`/api/redoc/`**

---

## Customer Experience

Customers **never need to log in**. They are identified by their **IP address**, which is automatically captured on every order.

| Feature | Detail |
|---|---|
| Visit tracking | `CustomerVisit` row per IP: name, visit count, first/last seen |
| Order history | All past orders linked to the customer's IP via `SalesRecord.ip_address` |
| Preferred name | Customer can set `POST /api/customer/update_name/` — persists across visits |
| Suggestions | `GET /api/customer/suggestions/` — personalised feed (see below) |

---

## Staff Authentication

```bash
# Login
POST /api/auth/login/
{ "username": "admin", "password": "<your-admin-password>" }
→ { "token": "abc123...", "role": "admin", "is_on_duty": true }

# All subsequent staff requests:
Authorization: Token abc123...
```

Default accounts created by `python manage.py create_staff`:

| Username | Env Variable | Role |
|---|---|---|
| `admin` | `ADMIN_PASSWORD` | Admin / Manager |
| `kitchen1` | `KITCHEN1_PASSWORD` | Kitchen Staff |
| `waiter1` | `WAITER1_PASSWORD` | Waiter |

Set the environment variables before running the command, or passwords will be
auto-generated and printed to stdout on first run.

> ⚠️ Always set strong passwords via environment variables before deploying to production.
> Auto-generated passwords are printed once to stdout on first run — treat that output as a secret
> and change passwords immediately using `python manage.py changepassword <username>`.

---

## QR Code Management

### Via Admin Panel
1. Go to **Admin → Tables**
2. Select tables → Action: **🔲 Generate / refresh QR codes** → Execute
3. Action: **🖨️ Print QR code sheet** → Opens a print-ready HTML page with all QR codes
4. Each QR code scans to the customer ordering URL for that table

### Via API
```
GET /api/tables/{id}/qr_code/
→ { "table_number": 5, "qr_url": "...", "qr_data_uri": "data:image/png;base64,..." }
```
The QR image is auto-generated on first access and cached on the `Table` row.

---

## Behaviour Tracking & Suggestions

`GET /api/customer/suggestions/` returns a rich payload with zero login required:

```json
{
  "ip_address": "192.168.1.10",
  "is_returning": true,
  "visit_count": 7,
  "preferred_name": "Alice",
  "welcome_message": "Welcome back, Alice! 👋 Great to see you again.",
  "reorder_items": [
    { "id": 3, "name": "Caramel Macchiato", "price": 220, "qty": 2 }
  ],
  "top_picks": [
    { "id": 3, "name": "Caramel Macchiato", "qty": 14, "price": 220 },
    { "id": 12, "name": "Margherita", "qty": 8, "price": 350 }
  ],
  "trending_now": [
    { "id": 1, "name": "Iced Latte", "price": 180, "emoji": "🧊", "category": "coffee" }
  ],
  "suggested_items": [ ... ],
  "previous_orders": [ ... ]
}
```

The **customer ordering page** (`frontend/customer.html`) reads this on load and:
- Shows a personalised welcome banner
- Pre-fills a "Reorder" quick-add section for the last order
- Displays "Your favourites" based on order history
- Shows globally trending items

---

## Database & SQL Schema

See [`backend/schema.sql`](backend/schema.sql) for the full DDL.

### Tables
`cafe_menuitem` · `cafe_table` · `cafe_reservation` · `cafe_tablesession` · `cafe_sessionitem` · `cafe_kitchenorder` · `cafe_kitchenorderitem` · `cafe_discount` · `cafe_salesrecord` · `cafe_orderfeedback` · `cafe_customervisit` · `cafe_staffprofile` · `cafe_cafesettings`

### SQL Views (created by migration)
| View | Description |
|---|---|
| `v_daily_revenue` | Daily revenue aggregation (order count, total, avg, discounts) |
| `v_popular_items` | Items ranked by total quantity sold, with revenue |
| `v_table_status` | Table occupancy: status, current customer, minutes occupied |

---

## Frontend Pages

| File | Description |
|---|---|
| `frontend/index.html` | Welcome / landing page with navigation |
| `frontend/customer.html` | Customer ordering page — browse menu, add to cart, apply discount, checkout |
| `frontend/kitchen.html` | Kitchen Display System — live order tickets, status updates |
| `frontend/admin.html` | Staff dashboard — tables, sessions, sales, menu management, analytics |
| `frontend/data.js` | Complete async API layer (30+ methods covering all endpoints) |

The frontend auto-detects the API URL from `window.SK_API_BASE` (defaults to `http://127.0.0.1:8000`).

---

## Admin Panel

`http://127.0.0.1:8000/admin/` — Django Admin with:

| Section | Features |
|---|---|
| **Menu Items** | Inline edit price/stock/trending; bulk trending/stock actions |
| **Tables** | Quick status edit; **Generate QR codes**; **Print QR code sheet**; QR preview in change form |
| **Reservations** | Date hierarchy; bulk confirm/cancel |
| **Kitchen Orders** | Priority filter; bulk complete; inline order items |
| **Sales Records** | Read-only; date hierarchy; tax amount display |
| **Discounts** | Code management; validity tracking |
| **Feedback** | Rating filters |
| **Staff Profiles** | Role + on-duty status management |
| **Customer Visits** | IP browse; visit counts; preferred names |
| **Cafe Settings** | Singleton — tax rate, name, branding, UPI ID |

---

## Testing

```bash
cd backend
python manage.py test cafe
```

**105 tests** covering:
- All model validations and business logic
- All API endpoints (CRUD, actions, filters)
- Staff authentication (login, logout, me, toggle_duty)
- Customer IP tracking (me, orders, update_name, suggestions)
- Permission enforcement (admin-only, kitchen-or-admin, public)
- Discount validation (percentage, fixed, expired, exhausted)
- Reservation conflict detection
- Bill calculation (subtotal, discount, tax, rounding)
- Kitchen order bulk updates
- Stats and analytics endpoints
- QR code utilities

---

## Configuration

Key `settings.py` options (override via environment variables):

| Setting | Env Variable | Default |
|---|---|---|
| Secret key | `DJANGO_SECRET_KEY` | insecure dev key |
| Debug mode | `DJANGO_DEBUG` | `True` |
| Allowed hosts | `DJANGO_ALLOWED_HOSTS` | `localhost 127.0.0.1` |
| CORS origins | `CORS_ALLOWED_ORIGINS` | localhost:3000, 8080 |
| Database | — | SQLite `db.sqlite3` |
| Time zone | — | `Asia/Kolkata` |
| Tax rate | — | 5% (via CafeSettings singleton) |

For **PostgreSQL** in production, update `DATABASES` in `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

---

## Deployment

1. Set `DJANGO_DEBUG=False` and a strong `DJANGO_SECRET_KEY`
2. Set `DJANGO_ALLOWED_HOSTS` to your domain
3. Configure PostgreSQL (recommended for production)
4. Run `python manage.py collectstatic`
5. Serve with **gunicorn** + **nginx**

```bash
gunicorn cafe_backend.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

Set `window.SK_API_BASE = 'https://your-api.example.com'` in the frontend HTML before loading `data.js`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Django 6.0.3 |
| REST API | Django REST Framework 3.16.1 |
| API docs | drf-spectacular (Swagger / ReDoc) |
| Filtering | django-filter 25.2 |
| CORS | django-cors-headers |
| QR codes | qrcode 8.2 + Pillow 12.1.1 |
| Database (dev) | SQLite 3 |
| Database (prod) | PostgreSQL (recommended) |
| Frontend | HTML5 / CSS3 / Vanilla JS |
| Auth | DRF Token Authentication |

---

*# SK cafe Management System — built with ☕ and Django*
