# # SK cafe — Django Backend API  `v3.0`

A **production-grade** Django REST Framework backend for the **# SK cafe** management system.

## Quick Start

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_menu       # 27 menu items + 12 tables
python manage.py create_staff    # admin / kitchen1 / waiter1 accounts
python manage.py runserver
```

- API: `http://127.0.0.1:8000/api/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- Admin: `http://127.0.0.1:8000/admin/`

## Models

| Model | Description |
|---|---|
| `MenuItem` | Menu item (name, price, category, veg, stock, trending) |
| `Table` | Physical dining table with QR code |
| `Reservation` | Table reservation (date/time, party size, status) |
| `TableSession` | Active dine-in/takeaway/delivery order session |
| `SessionItem` | Line item inside a session (menu item + qty + price snapshot) |
| `KitchenOrder` | Kitchen ticket auto-created when items are ordered |
| `KitchenOrderItem` | Line item within a kitchen ticket |
| `Discount` | Promotional code (percentage or fixed, date-limited) |
| `SalesRecord` | Archived closed session (full item snapshot + totals) |
| `OrderFeedback` | Post-visit customer rating linked to a SalesRecord |
| `CafeSettings` | Singleton: tax rate, cafe name, UPI ID, hours |
| `StaffProfile` | Extended profile for staff (role: admin/kitchen/waiter) |
| `CustomerVisit` | Anonymous customer tracked by IP address |

All domain models inherit from `BaseModel` (`created_at`, `updated_at`, `is_active`).

## Endpoints

### Auth (staff only)
```
POST   /api/auth/login/         → { token, username, role, is_on_duty }
POST   /api/auth/logout/        → revoke token
GET    /api/auth/me/            → current user profile
POST   /api/auth/toggle_duty/   → flip on-duty flag
```

### Menu
```
GET    /api/menu/               → list (filter: category, in_stock, trending; search: name)
POST   /api/menu/               → create item
GET    /api/menu/{id}/          → detail
PATCH  /api/menu/{id}/          → partial update
DELETE /api/menu/{id}/          → delete
POST   /api/menu/{id}/toggle_stock/     → flip in_stock
POST   /api/menu/{id}/toggle_trending/  → flip trending
```

### Tables
```
GET    /api/tables/             → list all tables
POST   /api/tables/             → create table
GET    /api/tables/{id}/        → detail
PATCH  /api/tables/{id}/        → update
DELETE /api/tables/{id}/        → delete
GET    /api/tables/{id}/session/     → active session for this table
GET    /api/tables/{id}/qr_redirect/ → customer ordering URL
GET    /api/tables/{id}/qr_code/     → QR code PNG (base64 data URI)
```

### Sessions (keyed by table number)
```
GET    /api/sessions/                       → list all active sessions
GET    /api/sessions/{table_num}/           → get session
POST   /api/sessions/{table_num}/           → add items (creates session if needed)
POST   /api/sessions/{table_num}/close/     → close + archive as SalesRecord
POST   /api/sessions/{table_num}/mark_bill_printed/
GET    /api/sessions/{table_num}/generate_bill/
```

### Kitchen
```
GET    /api/kitchen/                    → list orders (filter: status, priority)
GET    /api/kitchen/{id}/               → detail
PATCH  /api/kitchen/{id}/               → update order
PATCH  /api/kitchen/{id}/status/        → update status only
POST   /api/kitchen/bulk_update/        → { ids: [], status: "completed" }
```

### Reservations
```
GET/POST   /api/reservations/
GET/PATCH/DELETE /api/reservations/{id}/
POST       /api/reservations/{id}/confirm/
POST       /api/reservations/{id}/seat/
POST       /api/reservations/{id}/cancel/
```

### Customer (no login — IP-based)
```
GET    /api/customer/me/            → visit profile (count, name, dates)
GET    /api/customer/orders/        → past orders for this IP
POST   /api/customer/update_name/   → { name: "Alice" }
GET    /api/customer/suggestions/   → personalised recommendations feed
```

### Discounts
```
GET/POST   /api/discounts/
GET/PATCH/DELETE /api/discounts/{id}/
POST       /api/discounts/validate/   → { code, subtotal } → discount amount
```

### Sales (read-only)
```
GET    /api/sales/      → list (filter: date range, payment method)
GET    /api/sales/{id}/
```

### Feedback
```
GET    /api/feedback/
GET    /api/feedback/{id}/
POST   /api/feedback/   → { session_record, table_num, overall_rating, ... }
```

### Stats
```
GET    /api/stats/                    → today: revenue, orders, avg, active tables
GET    /api/stats/top_items/          → top 10 by qty sold
GET    /api/stats/hourly/             → revenue by hour today
GET    /api/stats/category_breakdown/ → revenue per category
```

### Settings (admin only for writes)
```
GET    /api/settings/
POST   /api/settings/   → partial update (name, tax_rate, UPI ID, etc.)
```

## Permissions

| Endpoint group | Permission |
|---|---|
| Menu (reads) | Public |
| Sessions (create/read) | Public |
| Customer endpoints | Public |
| Discounts (validate) | Public |
| Feedback (read/write) | Public |
| Kitchen (read/update) | `IsKitchenOrAdmin` |
| Discounts (create/edit/delete) | `IsAdminStaff` |
| Settings (write) | `IsAdminStaff` |
| Sales (read) | `IsStaffMember` |
| Auth (logout/me) | `IsAuthenticated` |

## QR Code Management

QR codes are stored per-table as base64 PNG data URIs in `Table.qr_code_data`.

**Admin actions** (Admin → Tables → select → action):
- 🔲 **Generate / refresh QR codes** — creates/updates QR for selected tables
- 🖨️ **Print QR code sheet** — opens a print-ready HTML page with all QR images

**API**: `GET /api/tables/{id}/qr_code/` — auto-generates and caches on first access.

## Customer Behaviour Tracking

`GET /api/customer/suggestions/` returns a Zomato-style personalised feed:

```json
{
  "welcome_message": "Welcome back, Alice! 👋",
  "is_returning": true,
  "reorder_items": [...],       // last order items for quick re-order
  "top_picks": [...],           // customer's personal most-ordered items
  "trending_now": [...],        // globally trending menu items
  "suggested_items": [...],     // merged personalised list
  "previous_orders": [...]      // last 5 sales records
}
```

## Testing

```bash
python manage.py test cafe
```

**105 tests** — all models, endpoints, auth, permissions, IP tracking, QR utils, bill logic.

## Management Commands

| Command | Description |
|---|---|
| `seed_menu` | Seed 27 menu items across all categories |
| `seed_menu --reset` | Wipe and re-seed menu |
| `seed_tables` | Seed 12 dining tables |
| `create_staff` | Create admin / kitchen1 / waiter1 accounts |

## Dependencies

```
Django==6.0.3
djangorestframework==3.16.1
django-cors-headers==4.9.0
django-filter==25.2
drf-spectacular==0.29.0
qrcode[pil]==8.2
Pillow==12.1.1
```
