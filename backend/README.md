# SK Cafe – Django Backend API  `v2.0`

A **production-grade** Django REST Framework backend for the **SK Cafe** management system, built to senior-developer standards.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| Framework | Django 6.0 + Django REST Framework 3.16 |
| Filtering | django-filter 25.2 |
| API Docs | drf-spectacular 0.29 (Swagger + ReDoc) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Timezone | Asia/Kolkata (IST) |

---

## Features at a Glance

| Module | Highlights |
|--------|-----------|
| **Menu** | CRUD, category filter, search, stock toggle, trending toggle, allergens, prep time |
| **Tables** | Physical table management, QR code URL per table, status tracking |
| **Reservations** | Full booking workflow: pending → confirmed → seated → completed / cancelled |
| **Sessions** | Cart management, multi-item orders, discount code support, bill breakdown |
| **Kitchen (KDS)** | Priority queuing (normal/high/urgent), bulk status update, estimated time |
| **Discounts** | Percentage or fixed-amount promo codes, expiry, usage limits, live validation |
| **Feedback** | 1-5 star ratings (food, service, overall), recommendations |
| **Sales Records** | Archived sessions with payment method, discount tracking |
| **Analytics** | Today's stats, top items, revenue by hour, revenue by category |
| **Settings** | Cafe info, tax rate, opening/closing times, UPI ID, footer message |
| **API Docs** | Swagger UI at `/api/docs/` • ReDoc at `/api/redoc/` • OpenAPI at `/api/schema/` |

---

## Project Structure

```
backend/
├── manage.py
├── requirements.txt
├── README.md
├── cafe_backend/              # Django project
│   ├── settings.py            # All configuration (env-aware)
│   ├── urls.py                # Root URL routing + Swagger URLs
│   ├── wsgi.py
│   └── asgi.py
└── cafe/                      # Main application
    ├── models.py              # All domain models (with BaseModel mixin)
    ├── serializers.py         # DRF serializers for all models
    ├── views.py               # All ViewSets with @extend_schema docs
    ├── urls.py                # Router + custom session/table URLs
    ├── admin.py               # Professional Django admin
    ├── filters.py             # FilterSets (MenuItem, KitchenOrder, ...)
    ├── exceptions.py          # Custom API exceptions
    ├── utils.py               # calculate_bill(), generate_qr_url(), get_greeting()
    ├── signals.py             # Business logic signal handlers
    ├── apps.py                # AppConfig registering signals
    ├── tests.py               # 79 unit/integration tests
    └── management/
        └── commands/
            ├── seed_menu.py   # Load default 27 menu items
            └── seed_tables.py # Create 12 tables with locations
```

---

## Quick Start

```bash
# 1. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. Seed initial data
python manage.py seed_menu    # loads 27 menu items + cafe settings
python manage.py seed_tables  # creates 12 tables

# 5. Create a superuser for the admin panel
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Server: **http://127.0.0.1:8000/**  
Admin: **http://127.0.0.1:8000/admin/**  
Swagger UI: **http://127.0.0.1:8000/api/docs/**  
ReDoc: **http://127.0.0.1:8000/api/redoc/**

---

## Data Models

### `BaseModel` (abstract)
Every domain model inherits from `BaseModel`:
- `created_at` – auto-set on creation
- `updated_at` – auto-updated on save
- `is_active` – soft-delete flag

### Domain Models

| Model | Key Fields | New in v2 |
|-------|------------|-----------|
| `MenuItem` | name, price, category, emoji, is_veg, in_stock, trending | allergens, serving_size, preparation_time_minutes, sort_order |
| `Table` | number, capacity, location, status, qr_code_url | ✅ New |
| `Reservation` | table, customer_name, phone, party_size, date, time, status | ✅ New |
| `TableSession` | table_num, customer_name, items, bill_printed | session_type, discount_code, discount_amount |
| `SessionItem` | session, menu_item, qty, price | notes |
| `KitchenOrder` | table_num, status, items | priority, estimated_minutes, notes |
| `KitchenOrderItem` | order, name, qty, price | notes |
| `Discount` | code, discount_type, value, valid_from/until, max_uses | ✅ New |
| `OrderFeedback` | session_record, ratings (food/service/overall), comment | ✅ New |
| `SalesRecord` | table_num, items_json, subtotal, total | payment_method, discount_amount |
| `CafeSettings` | cafe_name, tax_rate, gst, total_tables | opening/closing time, UPI ID, footer |

---

## Complete API Reference

**Base URL:** `/api/`  
**Interactive docs:** `/api/docs/` (Swagger UI)

All list endpoints support:
- **Pagination**: `?page=1&page_size=20`
- **Search**: `?search=<term>` (where applicable)
- **Ordering**: `?ordering=price` or `?ordering=-created_at`
- **Filtering**: model-specific query params (see FilterSets)

---

### 🍽️ Menu — `/api/menu/`

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/menu/` | List items • `?category=coffee&is_veg=true&in_stock=true&price__lte=300` |
| POST | `/api/menu/` | Create item |
| GET | `/api/menu/{id}/` | Get one item |
| PUT/PATCH | `/api/menu/{id}/` | Update item |
| DELETE | `/api/menu/{id}/` | Delete item |
| POST | `/api/menu/{id}/toggle_stock/` | Toggle in-stock |
| POST | `/api/menu/{id}/toggle_trending/` | Toggle trending |

---

### 🪑 Tables — `/api/tables/`

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/tables/` | List all tables |
| POST | `/api/tables/` | Create a table |
| GET | `/api/tables/{id}/` | Get table details |
| PATCH | `/api/tables/{id}/` | Update table |
| GET | `/api/tables/{number}/qr_redirect/` | Customer ordering URL for QR code |

---

### 📅 Reservations — `/api/reservations/`

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/reservations/` | List reservations • `?reserved_date=2026-03-07&status=confirmed` |
| POST | `/api/reservations/` | Create booking |
| GET | `/api/reservations/{id}/` | Get booking |
| PATCH | `/api/reservations/{id}/` | Update booking |
| POST | `/api/reservations/{id}/confirm/` | Confirm pending reservation |
| POST | `/api/reservations/{id}/seat/` | Mark as seated |
| POST | `/api/reservations/{id}/cancel/` | Cancel |

**POST body for creating a reservation:**
```json
{
  "table": 1,
  "customer_name": "Alice",
  "customer_phone": "+91 9876543210",
  "party_size": 4,
  "reserved_date": "2026-03-07",
  "reserved_time": "19:00",
  "notes": "Birthday celebration, window seat please"
}
```

---

### 🛒 Table Sessions — `/api/sessions/`

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/sessions/` | All active sessions |
| GET | `/api/sessions/{table}/` | Session for a table |
| POST | `/api/sessions/{table}/` | Create/update session & add items |
| GET | `/api/sessions/{table}/generate_bill/` | Full bill breakdown |
| POST | `/api/sessions/{table}/close/` | Close → archive as SalesRecord |
| POST | `/api/sessions/{table}/mark_bill_printed/` | Flag as printed |

**POST body for `/api/sessions/{table}/`:**
```json
{
  "customer_name": "Alice",
  "special_instructions": "No onions",
  "session_type": "dine_in",
  "discount_code": "WELCOME10",
  "items": [
    {"id": 1, "qty": 2, "notes": "Extra hot"},
    {"id": 10, "qty": 1}
  ]
}
```

**Bill breakdown response:**
```json
{
  "table_num": 5,
  "customer_name": "Alice",
  "items": [...],
  "subtotal": 360,
  "discount": 36,
  "tax": 16,
  "total": 340
}
```

---

### 👨‍🍳 Kitchen Orders — `/api/kitchen/`

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/kitchen/` | List orders • `?status=pending&priority=high` |
| PATCH | `/api/kitchen/{id}/status/` | `{"status": "preparing"}` |
| POST | `/api/kitchen/bulk_update/` | `{"ids": [1,2,3], "status": "completed"}` |
| DELETE | `/api/kitchen/{id}/` | Delete order |

**Status flow:** `pending` → `preparing` → `completed`

---

### 🏷️ Discounts — `/api/discounts/`

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/discounts/` | List all discount codes |
| POST | `/api/discounts/` | Create discount code |
| GET | `/api/discounts/{id}/` | Get code details |
| PATCH | `/api/discounts/{id}/` | Update |
| DELETE | `/api/discounts/{id}/` | Delete |
| POST | `/api/discounts/validate/` | Validate a code |

**POST /api/discounts/validate/:**
```json
{ "code": "WELCOME10", "subtotal": 500 }
```
Response:
```json
{
  "valid": true,
  "code": "WELCOME10",
  "discount_amount": 50,
  "discount_type": "percentage",
  "value": "10.00",
  "description": "Welcome 10% off"
}
```

---

### ⭐ Feedback — `/api/feedback/`

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/feedback/` | List all feedback |
| POST | `/api/feedback/` | Submit feedback |

**POST body:**
```json
{
  "session_record": 1,
  "table_num": 5,
  "overall_rating": 5,
  "food_rating": 5,
  "service_rating": 4,
  "comment": "Amazing biryani!",
  "would_recommend": true
}
```

---

### 💰 Sales Records — `/api/sales/`

Read-only. Filter with `?table_num=5&payment_method=upi&closed_at__date__gte=2026-03-01`

---

### 📊 Analytics — `/api/stats/`

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/stats/` | Today: revenue, orders, avg, active tables, avg rating |
| GET | `/api/stats/top_items/` | Top 10 items by quantity sold |
| GET | `/api/stats/hourly/` | Revenue distribution by hour (today) |
| GET | `/api/stats/category_breakdown/` | Revenue & order count by food category |

---

### ⚙️ Settings — `/api/settings/`

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/settings/` | Get current settings |
| POST | `/api/settings/` | Update (partial accepted) |

---

## Running Tests

```bash
python manage.py test cafe          # run all 79 tests
python manage.py test cafe -v 2     # verbose output
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | dev key | Django secret key (change in production!) |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost 127.0.0.1` | Space-separated allowed hosts |
| `CORS_ALLOWED_ORIGINS` | localhost variants | Space-separated CORS origins |

---

## Production Checklist

- [ ] Set `DJANGO_SECRET_KEY` to a strong random key
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Set `DJANGO_ALLOWED_HOSTS` to your domain
- [ ] Configure PostgreSQL via `DATABASES` setting
- [ ] Set `CORS_ALLOWED_ORIGINS` to your frontend domain
- [ ] Run `python manage.py collectstatic`
- [ ] Use Gunicorn or uWSGI as WSGI server
- [ ] Put Nginx in front as a reverse proxy
- [ ] Set up periodic task to back up `db.sqlite3` (if using SQLite)


This is the **Django REST Framework** backend for the **SK Cafe** management system.

## Features

| Module | Endpoints |
|---|---|
| **Menu** | CRUD, category filter, stock toggle |
| **Table Sessions** | Create, view, add items, close (generates SalesRecord) |
| **Kitchen Orders** | Automatic on order, status updates (pending → preparing → completed) |
| **Sales Records** | Read-only archive of closed sessions |
| **Analytics** | Today's revenue, order count, active tables, average order value |
| **Cafe Settings** | Name, phone, address, GST, tax rate, total tables |

## Project Structure

```
backend/
├── manage.py
├── requirements.txt
├── cafe_backend/          # Django project settings & routing
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── cafe/                  # Main app
    ├── models.py          # MenuItem, TableSession, SessionItem,
    │                      #   KitchenOrder, SalesRecord, CafeSettings
    ├── serializers.py
    ├── views.py           # ViewSets
    ├── urls.py            # Router + custom session URLs
    ├── admin.py           # Django admin registration
    └── management/
        └── commands/
            └── seed_menu.py   # Load default menu items
```

## Quick Start

```bash
# 1. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. Seed the default menu
python manage.py seed_menu

# 5. Create a superuser for the admin panel
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Server starts at **http://127.0.0.1:8000/**.

## API Reference

### Base URL: `/api/`

#### Menu Items

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/menu/` | List all menu items (`?category=coffee`) |
| POST | `/api/menu/` | Create a menu item |
| GET | `/api/menu/{id}/` | Get one item |
| PUT/PATCH | `/api/menu/{id}/` | Update item |
| DELETE | `/api/menu/{id}/` | Delete item |
| POST | `/api/menu/{id}/toggle_stock/` | Toggle in-stock flag |

#### Table Sessions

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/sessions/` | List all active sessions |
| GET | `/api/sessions/{table}/` | Get session for a table |
| POST | `/api/sessions/{table}/` | Create/update session & add items |
| POST | `/api/sessions/{table}/close/` | Close session → creates SalesRecord |
| POST | `/api/sessions/{table}/mark_bill_printed/` | Flag bill as printed |

**POST body for `/api/sessions/{table}/`:**
```json
{
  "customer_name": "Alice",
  "special_instructions": "No onions",
  "items": [
    {"id": 1, "qty": 2},
    {"id": 10, "qty": 1}
  ]
}
```

#### Kitchen Orders

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/kitchen/` | List orders (`?status=pending`) |
| PATCH | `/api/kitchen/{id}/status/` | Update status |

**PATCH body:** `{"status": "preparing"}` or `{"status": "completed"}`

#### Sales Records

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/sales/` | List all archived sales |
| GET | `/api/sales/{id}/` | Get one record |

#### Stats

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/stats/` | Today's revenue, order count, active tables, avg order |

#### Settings

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/settings/` | Get cafe settings |
| POST | `/api/settings/` | Update settings (partial) |

## Django Admin

Available at **http://127.0.0.1:8000/admin/** after creating a superuser.

All models are registered with sensible list displays and inline editing.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | dev key | Django secret key |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost 127.0.0.1` | Space-separated allowed hosts |
| `CORS_ALLOWED_ORIGINS` | localhost variants | Space-separated CORS origins |

## Database

Uses **SQLite** by default (`db.sqlite3`). For production, configure PostgreSQL via the standard `DATABASES` Django setting.
