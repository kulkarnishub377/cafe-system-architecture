"""
Menu item recommendation engine for The Bean & Brew Café.

Provides collaborative and time-based recommendations using Django ORM.
"""

from __future__ import annotations

import datetime
from typing import Any

from django.db.models import Count
from django.utils import timezone

from .models import MenuItem, SessionItem, TableSession


class MenuRecommender:
    """Recommendation helpers for menu items."""

    def frequently_ordered_together(self, item_id: int) -> list[dict[str, Any]]:
        """Return items that are frequently ordered in the same session as *item_id*.

        Args:
            item_id: The MenuItem pk to find co-ordered items for.

        Returns:
            A list of dicts with keys ``id``, ``name``, and ``co_order_count``,
            sorted by co_order_count descending.
        """
        sessions_with_item = (
            SessionItem.objects.filter(menu_item_id=item_id)
            .values_list("session_id", flat=True)
        )
        co_items = (
            SessionItem.objects.filter(session_id__in=sessions_with_item)
            .exclude(menu_item_id=item_id)
            .values("menu_item__id", "menu_item__name")
            .annotate(co_order_count=Count("id"))
            .order_by("-co_order_count")[:10]
        )
        return [
            {
                "id": r["menu_item__id"],
                "name": r["menu_item__name"],
                "co_order_count": r["co_order_count"],
            }
            for r in co_items
        ]

    def popular_at_time(self, hour: int | None = None) -> list[dict[str, Any]]:
        """Return items popular at a given hour of the day.

        Args:
            hour: Hour (0–23). Defaults to the current hour.

        Returns:
            A list of dicts with keys ``id``, ``name``, and ``order_count``.
        """
        if hour is None:
            hour = timezone.now().hour

        items = (
            SessionItem.objects.filter(created_at__hour=hour)
            .values("menu_item__id", "menu_item__name")
            .annotate(order_count=Count("id"))
            .order_by("-order_count")[:10]
        )
        return [
            {
                "id": r["menu_item__id"],
                "name": r["menu_item__name"],
                "order_count": r["order_count"],
            }
            for r in items
        ]

    def personalized_for_customer(self, customer_name: str) -> list[dict[str, Any]]:
        """Return item recommendations based on a customer's past orders.

        Looks up TableSession records matching *customer_name* and returns
        items they have ordered most often.

        Args:
            customer_name: The customer's name as stored on TableSession.

        Returns:
            A list of dicts with keys ``id``, ``name``, and ``order_count``.
        """
        sessions = TableSession.objects.filter(
            customer_name__iexact=customer_name
        ).values_list("id", flat=True)

        items = (
            SessionItem.objects.filter(session_id__in=sessions)
            .values("menu_item__id", "menu_item__name")
            .annotate(order_count=Count("id"))
            .order_by("-order_count")[:10]
        )
        return [
            {
                "id": r["menu_item__id"],
                "name": r["menu_item__name"],
                "order_count": r["order_count"],
            }
            for r in items
        ]

    def trending_today(self) -> list[dict[str, Any]]:
        """Return items with a spike in orders today compared to yesterday.

        Returns:
            A list of dicts with keys ``id``, ``name``, ``today``,
            ``yesterday``, and ``growth_pct``.
        """
        today = timezone.localdate()
        yesterday = today - datetime.timedelta(days=1)

        def _counts(date: datetime.date):
            return {
                r["menu_item__id"]: r["count"]
                for r in (
                    SessionItem.objects.filter(created_at__date=date)
                    .values("menu_item__id")
                    .annotate(count=Count("id"))
                )
            }

        today_counts = _counts(today)
        yesterday_counts = _counts(yesterday)

        results = []
        for item_id, today_count in today_counts.items():
            yesterday_count = yesterday_counts.get(item_id, 0)
            growth = (
                ((today_count - yesterday_count) / yesterday_count * 100)
                if yesterday_count > 0
                else 100.0
            )
            if growth > 0:
                try:
                    item = MenuItem.objects.get(pk=item_id)
                    results.append(
                        {
                            "id": item_id,
                            "name": item.name,
                            "today": today_count,
                            "yesterday": yesterday_count,
                            "growth_pct": round(growth, 1),
                        }
                    )
                except MenuItem.DoesNotExist:
                    pass

        return sorted(results, key=lambda x: x["growth_pct"], reverse=True)

    def get_upsell_suggestions(self, cart_items: list[int]) -> list[dict[str, Any]]:
        """Suggest add-on items for the current cart.

        Args:
            cart_items: A list of MenuItem pks currently in the cart.

        Returns:
            A list of dicts with keys ``id``, ``name``, ``price``,
            and ``emoji`` for suggested add-ons not already in the cart.
        """
        sessions_with_any = (
            SessionItem.objects.filter(menu_item_id__in=cart_items)
            .values_list("session_id", flat=True)
            .distinct()
        )
        suggestions = (
            SessionItem.objects.filter(session_id__in=sessions_with_any)
            .exclude(menu_item_id__in=cart_items)
            .values("menu_item__id", "menu_item__name",
                    "menu_item__price", "menu_item__emoji")
            .annotate(freq=Count("id"))
            .order_by("-freq")[:5]
        )
        return [
            {
                "id": r["menu_item__id"],
                "name": r["menu_item__name"],
                "price": r["menu_item__price"],
                "emoji": r["menu_item__emoji"],
            }
            for r in suggestions
        ]
