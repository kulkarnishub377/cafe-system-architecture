-- # 91 VRS Cafe — Database Schema Reference
-- Generated for documentation and analytics.
-- SQLite dialect (managed by Django ORM for core tables).

-- -----------------------------------------------------------------------
-- Analytics views (created by migration 0002)
-- -----------------------------------------------------------------------

CREATE VIEW IF NOT EXISTS cafe_daily_sales AS
SELECT
    date(closed_at)      AS sale_date,
    COUNT(*)             AS orders,
    SUM(total)           AS revenue,
    AVG(total)           AS avg_order,
    SUM(discount_amount) AS total_discounts
FROM cafe_salesrecord
GROUP BY date(closed_at);

CREATE VIEW IF NOT EXISTS cafe_customer_ip_summary AS
SELECT
    ip_address,
    COUNT(*)       AS visits,
    SUM(total)     AS lifetime_spend,
    MAX(closed_at) AS last_visit
FROM cafe_salesrecord
WHERE ip_address IS NOT NULL
GROUP BY ip_address;
