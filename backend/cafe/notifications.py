"""
Internal notification and alerting system for The Bean & Brew Café.

Uses Python dataclasses and the standard logging module.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

_active_alerts: list["Notification"] = []


@dataclass
class Notification:
    """Represents a single cafe notification or alert."""

    type: str
    message: str
    severity: str  # "info" | "warning" | "error"
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)


class NotificationService:
    """Service for creating and retrieving cafe notifications."""

    def order_placed(self, session: Any) -> Notification:
        """Create a notification when a new order is placed.

        Args:
            session: A TableSession instance.

        Returns:
            The created Notification object.
        """
        msg = f"New order placed for Table {session.table_num}"
        n = Notification(type="order_placed", message=msg, severity="info",
                         data={"table_num": session.table_num})
        _active_alerts.append(n)
        logger.info(msg)
        return n

    def order_ready(self, kitchen_order: Any) -> Notification:
        """Create a notification when a kitchen order is ready.

        Args:
            kitchen_order: A KitchenOrder instance.

        Returns:
            The created Notification object.
        """
        msg = f"Order #{kitchen_order.id} for Table {kitchen_order.table_num} is ready!"
        n = Notification(type="order_ready", message=msg, severity="info",
                         data={"order_id": kitchen_order.id,
                               "table_num": kitchen_order.table_num})
        _active_alerts.append(n)
        logger.info(msg)
        return n

    def table_waiting_long(self, table: Any, minutes: int) -> Notification:
        """Create a warning when a table has been waiting too long.

        Args:
            table: A Table instance or table number.
            minutes: How many minutes the table has been waiting.

        Returns:
            The created Notification object.
        """
        table_num = getattr(table, "number", table)
        msg = f"Table {table_num} has been waiting {minutes} minutes!"
        n = Notification(type="table_waiting", message=msg, severity="warning",
                         data={"table_num": table_num, "minutes": minutes})
        _active_alerts.append(n)
        logger.warning(msg)
        return n

    def daily_summary(self) -> Notification:
        """Generate a daily summary notification.

        Queries today's SalesRecord to build the summary.

        Returns:
            The created Notification object.
        """
        from django.utils import timezone
        from django.db.models import Sum, Count
        from .models import SalesRecord

        today = timezone.localdate()
        stats = SalesRecord.objects.filter(closed_at__date=today).aggregate(
            total_revenue=Sum("total"), total_orders=Count("id")
        )
        revenue = stats["total_revenue"] or 0
        orders = stats["total_orders"] or 0
        msg = (f"Daily summary: {orders} orders, ₹{revenue} revenue "
               f"on {today.strftime('%d %b %Y')}")
        n = Notification(type="daily_summary", message=msg, severity="info",
                         data={"date": str(today), "revenue": revenue, "orders": orders})
        _active_alerts.append(n)
        logger.info(msg)
        return n

    def get_active_alerts(self) -> list[Notification]:
        """Return all active (non-dismissed) notifications.

        Returns:
            A list of Notification objects.
        """
        return list(_active_alerts)
