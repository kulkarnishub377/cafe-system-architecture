"""
Inventory and stock management for The Bean & Brew Café.

Provides helpers to inspect and update menu item stock levels.
"""

from __future__ import annotations

import datetime
from typing import Any

from django.utils import timezone

from .models import MenuItem, SessionItem


class InventoryManager:
    """Helpers for managing menu item stock."""

    def get_out_of_stock(self):
        """Return a QuerySet of MenuItem objects where in_stock is False."""
        return MenuItem.objects.filter(in_stock=False, is_active=True)

    def get_low_activity_items(self, days: int = 30):
        """Return items that have not been ordered in the last *days* days.

        Returns a QuerySet of MenuItem objects.
        """
        cutoff = timezone.now() - datetime.timedelta(days=days)
        sold_ids = (
            SessionItem.objects.filter(created_at__gte=cutoff)
            .values_list("menu_item_id", flat=True)
            .distinct()
        )
        return MenuItem.objects.filter(is_active=True).exclude(id__in=sold_ids)

    def bulk_toggle_stock(self, item_ids: list[int], in_stock: bool) -> int:
        """Set in_stock to *in_stock* for all MenuItem rows in *item_ids*.

        Returns the number of rows updated.
        """
        count = MenuItem.objects.filter(id__in=item_ids).update(in_stock=in_stock)
        return count

    def get_stock_summary(self) -> dict[str, Any]:
        """Return a dict with in_stock and out_of_stock counts per category.

        Example::

            {
                "coffee": {"in_stock": 5, "out_of_stock": 1},
                ...
            }
        """
        summary: dict[str, dict[str, int]] = {}
        for item in MenuItem.objects.filter(is_active=True):
            cat = item.category
            if cat not in summary:
                summary[cat] = {"in_stock": 0, "out_of_stock": 0}
            key = "in_stock" if item.in_stock else "out_of_stock"
            summary[cat][key] += 1
        return summary

    def auto_restock_suggestions(self) -> list[dict[str, Any]]:
        """Return a list of suggestions for items that should be restocked.

        Each suggestion is a dict with keys ``id``, ``name``, and
        ``suggested_action``.
        """
        out_of_stock = self.get_out_of_stock()
        suggestions = []
        for item in out_of_stock:
            suggestions.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "suggested_action": "Restock and mark as available",
                }
            )
        return suggestions
