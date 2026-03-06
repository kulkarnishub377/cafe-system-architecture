"""
Analytics helpers for The Bean & Brew Café system.

Provides revenue, item, and customer analytics using Django ORM aggregations.
"""

from __future__ import annotations

import datetime
from typing import Any

from django.db.models import Avg, Count, Sum
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone

from .models import CustomerVisit, KitchenOrder, MenuItem, SalesRecord, SessionItem


class RevenueAnalytics:
    """Analytics helpers for revenue data."""

    def daily_revenue(self, days: int = 7) -> list[dict[str, Any]]:
        """Return daily revenue totals for the last *days* days.

        Returns a list of dicts with keys ``date`` and ``revenue``.
        """
        cutoff = timezone.now() - datetime.timedelta(days=days)
        records = (
            SalesRecord.objects.filter(closed_at__gte=cutoff)
            .annotate(day=TruncDate("closed_at"))
            .values("day")
            .annotate(revenue=Sum("total"))
            .order_by("day")
        )
        return [{"date": str(r["day"]), "revenue": r["revenue"] or 0} for r in records]

    def weekly_revenue(self) -> dict[str, Any]:
        """Return total revenue for the current ISO week."""
        today = timezone.localdate()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        total = SalesRecord.objects.filter(
            closed_at__date__gte=start_of_week
        ).aggregate(total=Sum("total"))["total"] or 0
        return {"week_start": str(start_of_week), "revenue": total}

    def monthly_revenue(self) -> dict[str, Any]:
        """Return total revenue for the current calendar month."""
        today = timezone.localdate()
        total = SalesRecord.objects.filter(
            closed_at__year=today.year,
            closed_at__month=today.month,
        ).aggregate(total=Sum("total"))["total"] or 0
        return {"year": today.year, "month": today.month, "revenue": total}

    def peak_hours(self) -> list[dict[str, Any]]:
        """Return the top-5 hours of day by order count.

        Returns a list of dicts with keys ``hour`` and ``orders``.
        """
        records = (
            SalesRecord.objects.annotate(hour=ExtractHour("closed_at"))
            .values("hour")
            .annotate(orders=Count("id"))
            .order_by("-orders")[:5]
        )
        return [{"hour": int(r["hour"]), "orders": r["orders"]} for r in records]

    def avg_order_value(self) -> float:
        """Return the all-time average order value in INR."""
        result = SalesRecord.objects.aggregate(avg=Avg("total"))["avg"]
        return round(float(result or 0), 2)


class ItemAnalytics:
    """Analytics helpers for menu items."""

    def top_selling_items(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the *limit* best-selling menu items by quantity sold.

        Returns a list of dicts with keys ``name``, ``category``, and ``qty_sold``.
        """
        items = (
            SessionItem.objects.values(
                "menu_item__id", "menu_item__name", "menu_item__category"
            )
            .annotate(qty_sold=Sum("qty"))
            .order_by("-qty_sold")[:limit]
        )
        return [
            {
                "id": r["menu_item__id"],
                "name": r["menu_item__name"],
                "category": r["menu_item__category"],
                "qty_sold": r["qty_sold"],
            }
            for r in items
        ]

    def slow_moving_items(self, days: int = 30) -> list[dict[str, Any]]:
        """Return menu items with zero orders in the last *days* days.

        Returns a list of dicts with keys ``id``, ``name``, and ``category``.
        """
        cutoff = timezone.now() - datetime.timedelta(days=days)
        sold_ids = (
            SessionItem.objects.filter(created_at__gte=cutoff)
            .values_list("menu_item_id", flat=True)
            .distinct()
        )
        items = MenuItem.objects.filter(is_active=True).exclude(id__in=sold_ids)
        return [
            {"id": i.id, "name": i.name, "category": i.category}
            for i in items
        ]

    def category_performance(self) -> list[dict[str, Any]]:
        """Return revenue and quantity sold grouped by menu category.

        Returns a list of dicts with keys ``category``, ``qty_sold``, and ``revenue``.
        """
        rows = (
            SessionItem.objects.values("menu_item__category")
            .annotate(qty_sold=Sum("qty"), revenue=Sum("price"))
            .order_by("-revenue")
        )
        return [
            {
                "category": r["menu_item__category"],
                "qty_sold": r["qty_sold"],
                "revenue": r["revenue"] or 0,
            }
            for r in rows
        ]


class CustomerAnalytics:
    """Analytics helpers for customer behaviour."""

    def repeat_customer_rate(self) -> float:
        """Return the fraction of customers with more than one visit (0.0–1.0)."""
        total = CustomerVisit.objects.count()
        if total == 0:
            return 0.0
        repeat = CustomerVisit.objects.filter(visit_count__gt=1).count()
        return round(repeat / total, 4)

    def avg_visit_frequency(self) -> float:
        """Return the average visit count across all tracked customers."""
        result = CustomerVisit.objects.aggregate(avg=Avg("visit_count"))["avg"]
        return round(float(result or 0), 2)

    def top_customers(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the *limit* most frequent customers.

        Returns a list of dicts with keys ``preferred_name``, ``ip_address``,
        and ``visit_count``.
        """
        customers = CustomerVisit.objects.order_by("-visit_count")[:limit]
        return [
            {
                "preferred_name": c.preferred_name or "Anonymous",
                "ip_address": c.ip_address,
                "visit_count": c.visit_count,
            }
            for c in customers
        ]
