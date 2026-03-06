-- ============================================================
-- # 91 VRS Cafe – Database Schema (SQLite-compatible SQL)
-- Generated from Django models for documentation purposes.
-- For production use, run: python manage.py migrate
-- ============================================================

-- Staff authentication (Django built-in)
-- auth_user, auth_token managed by Django

-- Menu Items
CREATE TABLE IF NOT EXISTS cafe_menuitem (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    DATETIME NOT NULL,
    updated_at    DATETIME NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT 1,
    name          VARCHAR(200) NOT NULL,
    price         INTEGER NOT NULL CHECK(price >= 0),
    category      VARCHAR(50) NOT NULL,
    image         VARCHAR(500),
    emoji         VARCHAR(10) NOT NULL DEFAULT '🍽️',
    is_veg        BOOLEAN NOT NULL DEFAULT 1,
    in_stock      BOOLEAN NOT NULL DEFAULT 1,
    trending      BOOLEAN NOT NULL DEFAULT 0,
    description   VARCHAR(300),
    calories      INTEGER,
    preparation_time_minutes SMALLINT NOT NULL DEFAULT 10,
    allergens     VARCHAR(300),
    serving_size  VARCHAR(100),
    sort_order    SMALLINT NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_menuitem_category ON cafe_menuitem(category);
CREATE INDEX IF NOT EXISTS idx_menuitem_in_stock ON cafe_menuitem(in_stock);
CREATE INDEX IF NOT EXISTS idx_menuitem_trending ON cafe_menuitem(trending);

-- Physical Tables
CREATE TABLE IF NOT EXISTS cafe_table (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    is_active  BOOLEAN NOT NULL DEFAULT 1,
    number     SMALLINT NOT NULL UNIQUE,
    capacity   SMALLINT NOT NULL DEFAULT 4,
    location   VARCHAR(100),
    status     VARCHAR(20) NOT NULL DEFAULT 'available'
               CHECK(status IN ('available','occupied','reserved','maintenance')),
    qr_code_url VARCHAR(500)
);

-- Reservations
CREATE TABLE IF NOT EXISTS cafe_reservation (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at     DATETIME NOT NULL,
    updated_at     DATETIME NOT NULL,
    is_active      BOOLEAN NOT NULL DEFAULT 1,
    table_id       INTEGER NOT NULL REFERENCES cafe_table(id),
    customer_name  VARCHAR(200) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    party_size     SMALLINT NOT NULL,
    reserved_date  DATE NOT NULL,
    reserved_time  TIME NOT NULL,
    notes          TEXT,
    status         VARCHAR(20) NOT NULL DEFAULT 'pending'
                   CHECK(status IN ('pending','confirmed','seated','completed','cancelled'))
);
CREATE INDEX IF NOT EXISTS idx_reservation_date   ON cafe_reservation(reserved_date);
CREATE INDEX IF NOT EXISTS idx_reservation_status ON cafe_reservation(status);

-- Table Sessions (active orders)
CREATE TABLE IF NOT EXISTS cafe_tablesession (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at           DATETIME NOT NULL,
    updated_at           DATETIME NOT NULL,
    is_active            BOOLEAN NOT NULL DEFAULT 1,
    table_num            SMALLINT NOT NULL UNIQUE,
    customer_name        VARCHAR(200),
    special_instructions TEXT,
    start_time           DATETIME NOT NULL,
    bill_printed         BOOLEAN NOT NULL DEFAULT 0,
    session_type         VARCHAR(20) NOT NULL DEFAULT 'dine_in'
                         CHECK(session_type IN ('dine_in','takeaway','delivery')),
    discount_code        VARCHAR(50),
    discount_amount      INTEGER NOT NULL DEFAULT 0,
    ip_address           VARCHAR(39)    -- IPv4 or IPv6
);
CREATE INDEX IF NOT EXISTS idx_tablesession_table_num ON cafe_tablesession(table_num);
CREATE INDEX IF NOT EXISTS idx_tablesession_ip        ON cafe_tablesession(ip_address);

-- Session Items (cart line items)
CREATE TABLE IF NOT EXISTS cafe_sessionitem (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  DATETIME NOT NULL,
    updated_at  DATETIME NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT 1,
    session_id  INTEGER NOT NULL REFERENCES cafe_tablesession(id) ON DELETE CASCADE,
    menu_item_id INTEGER NOT NULL REFERENCES cafe_menuitem(id),
    qty         SMALLINT NOT NULL DEFAULT 1 CHECK(qty >= 1),
    price       INTEGER NOT NULL,
    notes       VARCHAR(200),
    UNIQUE(session_id, menu_item_id)
);

-- Kitchen Orders
CREATE TABLE IF NOT EXISTS cafe_kitchenorder (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at           DATETIME NOT NULL,
    updated_at           DATETIME NOT NULL,
    is_active            BOOLEAN NOT NULL DEFAULT 1,
    table_num            SMALLINT NOT NULL,
    customer_name        VARCHAR(200),
    special_instructions TEXT,
    status               VARCHAR(20) NOT NULL DEFAULT 'pending'
                         CHECK(status IN ('pending','preparing','completed')),
    priority             VARCHAR(10) NOT NULL DEFAULT 'normal'
                         CHECK(priority IN ('normal','high','urgent')),
    estimated_minutes    SMALLINT,
    notes                TEXT,
    completed_at         DATETIME
);
CREATE INDEX IF NOT EXISTS idx_kitchenorder_status     ON cafe_kitchenorder(status);
CREATE INDEX IF NOT EXISTS idx_kitchenorder_created_at ON cafe_kitchenorder(created_at);

-- Kitchen Order Items
CREATE TABLE IF NOT EXISTS cafe_kitchenorderitem (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES cafe_kitchenorder(id) ON DELETE CASCADE,
    name     VARCHAR(200) NOT NULL,
    qty      SMALLINT NOT NULL DEFAULT 1,
    price    INTEGER NOT NULL,
    notes    VARCHAR(200)
);

-- Discount Codes
CREATE TABLE IF NOT EXISTS cafe_discount (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at       DATETIME NOT NULL,
    updated_at       DATETIME NOT NULL,
    is_active        BOOLEAN NOT NULL DEFAULT 1,
    code             VARCHAR(50) NOT NULL UNIQUE,
    description      VARCHAR(300),
    discount_type    VARCHAR(20) NOT NULL CHECK(discount_type IN ('percentage','fixed')),
    value            DECIMAL(8,2) NOT NULL,
    min_order_amount INTEGER NOT NULL DEFAULT 0,
    max_uses         INTEGER,
    used_count       INTEGER NOT NULL DEFAULT 0,
    valid_from       DATE NOT NULL,
    valid_until      DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_discount_code        ON cafe_discount(code);
CREATE INDEX IF NOT EXISTS idx_discount_valid_until ON cafe_discount(valid_until);

-- Sales Records (closed sessions)
CREATE TABLE IF NOT EXISTS cafe_salesrecord (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at           DATETIME NOT NULL,
    updated_at           DATETIME NOT NULL,
    is_active            BOOLEAN NOT NULL DEFAULT 1,
    table_num            SMALLINT NOT NULL,
    customer_name        VARCHAR(200),
    special_instructions TEXT,
    items_json           TEXT NOT NULL DEFAULT '[]',
    subtotal             INTEGER NOT NULL DEFAULT 0,
    discount_amount      INTEGER NOT NULL DEFAULT 0,
    total                INTEGER NOT NULL DEFAULT 0,
    payment_method       VARCHAR(20) NOT NULL DEFAULT 'cash'
                         CHECK(payment_method IN ('cash','card','upi')),
    start_time           DATETIME NOT NULL,
    closed_at            DATETIME NOT NULL,
    ip_address           VARCHAR(39)
);
CREATE INDEX IF NOT EXISTS idx_salesrecord_closed_at  ON cafe_salesrecord(closed_at);
CREATE INDEX IF NOT EXISTS idx_salesrecord_ip_address ON cafe_salesrecord(ip_address);

-- Order Feedback
CREATE TABLE IF NOT EXISTS cafe_orderfeedback (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT 1,
    session_record_id INTEGER NOT NULL REFERENCES cafe_salesrecord(id),
    table_num       SMALLINT NOT NULL,
    overall_rating  SMALLINT NOT NULL CHECK(overall_rating BETWEEN 1 AND 5),
    food_rating     SMALLINT         CHECK(food_rating BETWEEN 1 AND 5),
    service_rating  SMALLINT         CHECK(service_rating BETWEEN 1 AND 5),
    comment         TEXT,
    would_recommend BOOLEAN
);

-- Customer Visits (anonymous IP tracking)
CREATE TABLE IF NOT EXISTS cafe_customervisit (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address     VARCHAR(39) NOT NULL UNIQUE,
    preferred_name VARCHAR(200),
    visit_count    INTEGER NOT NULL DEFAULT 1,
    first_visit    DATETIME NOT NULL,
    last_seen      DATETIME NOT NULL,
    device_info    VARCHAR(500)
);
CREATE INDEX IF NOT EXISTS idx_customervisit_ip ON cafe_customervisit(ip_address);

-- Staff Profiles (linked to Django auth_user)
CREATE TABLE IF NOT EXISTS cafe_staffprofile (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL UNIQUE REFERENCES auth_user(id),
    role                VARCHAR(20) NOT NULL DEFAULT 'waiter'
                        CHECK(role IN ('admin','kitchen','waiter')),
    phone               VARCHAR(20),
    profile_picture_url VARCHAR(500),
    is_on_duty          BOOLEAN NOT NULL DEFAULT 0,
    created_at          DATETIME NOT NULL,
    updated_at          DATETIME NOT NULL
);

-- Cafe Settings (singleton)
CREATE TABLE IF NOT EXISTS cafe_cafesettings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cafe_name       VARCHAR(200) NOT NULL DEFAULT '# 91 VRS Cafe',
    phone           VARCHAR(30),
    address         VARCHAR(300),
    gst             VARCHAR(30),
    tax_rate        REAL NOT NULL DEFAULT 5.0,
    total_tables    SMALLINT NOT NULL DEFAULT 12,
    opening_time    TIME NOT NULL DEFAULT '09:00',
    closing_time    TIME NOT NULL DEFAULT '23:00',
    currency_symbol VARCHAR(5) NOT NULL DEFAULT '₹',
    footer_message  VARCHAR(300),
    upi_id          VARCHAR(100),
    instagram_url   VARCHAR(200)
);

-- ============================================================
-- Database Views (analytics helpers)
-- ============================================================

CREATE VIEW IF NOT EXISTS v_daily_revenue AS
SELECT
    date(closed_at)        AS sale_date,
    COUNT(*)               AS order_count,
    SUM(total)             AS total_revenue,
    AVG(total)             AS avg_order_value,
    SUM(discount_amount)   AS total_discounts
FROM cafe_salesrecord
GROUP BY date(closed_at)
ORDER BY sale_date DESC;

CREATE VIEW IF NOT EXISTS v_popular_items AS
SELECT
    json_extract(item.value, '$.name')              AS item_name,
    json_extract(item.value, '$.category')          AS category,
    SUM(json_extract(item.value, '$.qty'))          AS total_qty_sold,
    SUM(
      json_extract(item.value, '$.price') *
      json_extract(item.value, '$.qty')
    )                                               AS total_revenue
FROM cafe_salesrecord,
     json_each(cafe_salesrecord.items_json) AS item
GROUP BY json_extract(item.value, '$.name')
ORDER BY total_qty_sold DESC;

CREATE VIEW IF NOT EXISTS v_table_status AS
SELECT
    t.number,
    t.capacity,
    t.location,
    t.status                       AS table_status,
    s.customer_name,
    s.start_time                   AS session_start,
    ROUND(
      (julianday('now') - julianday(s.start_time)) * 24 * 60
    )                              AS minutes_occupied
FROM cafe_table t
LEFT JOIN cafe_tablesession s ON s.table_num = t.number
ORDER BY t.number;
