# # 91 VRS Cafe – Django Backend API

This is the **Django REST Framework** backend for the **# 91 VRS Cafe** management system.

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
