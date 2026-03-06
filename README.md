# # 91 VRS Cafe – Full-Stack System

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
