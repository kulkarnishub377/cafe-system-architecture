"""
Report generation for The Bean & Brew Café.

Supports text summaries and CSV exports of sales and reservation data.
"""

from __future__ import annotations

import csv
import datetime
import io
from typing import Any

from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Reservation, SalesRecord, SessionItem


class ReportGenerator:
    """Generates text and CSV reports from cafe data."""

    def daily_sales_report(self, date: datetime.date | None = None) -> dict[str, Any]:
        """Return a dict containing all daily sales statistics.

        Args:
            date: The date to report on. Defaults to today.

        Returns:
            A dict with keys ``date``, ``total_orders``, ``total_revenue``,
            ``avg_order_value``, ``top_items``, and ``payment_breakdown``.
        """
        if date is None:
            date = timezone.localdate()

        qs = SalesRecord.objects.filter(closed_at__date=date)
        stats = qs.aggregate(
            total_orders=Count("id"),
            total_revenue=Sum("total"),
            avg_order_value=Avg("total"),
        )

        payment_breakdown = list(
            qs.values("payment_method").annotate(count=Count("id"), revenue=Sum("total"))
        )

        top_items = list(
            SessionItem.objects.filter(created_at__date=date)
            .values("menu_item__name")
            .annotate(qty_sold=Sum("qty"))
            .order_by("-qty_sold")[:5]
        )

        return {
            "date": str(date),
            "total_orders": stats["total_orders"] or 0,
            "total_revenue": stats["total_revenue"] or 0,
            "avg_order_value": round(float(stats["avg_order_value"] or 0), 2),
            "payment_breakdown": payment_breakdown,
            "top_items": [
                {"name": r["menu_item__name"], "qty_sold": r["qty_sold"]}
                for r in top_items
            ],
        }

    def weekly_performance_report(self) -> dict[str, Any]:
        """Return a dict containing weekly performance statistics.

        Returns:
            A dict with keys ``week_start``, ``week_end``, ``total_orders``,
            ``total_revenue``, ``avg_daily_revenue``, and ``busiest_day``.
        """
        today = timezone.localdate()
        week_start = today - datetime.timedelta(days=today.weekday())
        week_end = week_start + datetime.timedelta(days=6)

        qs = SalesRecord.objects.filter(
            closed_at__date__gte=week_start, closed_at__date__lte=week_end
        )
        stats = qs.aggregate(total_orders=Count("id"), total_revenue=Sum("total"))

        daily = (
            qs.annotate(day=TruncDate("closed_at"))
            .values("day")
            .annotate(revenue=Sum("total"))
            .order_by("-revenue")
        )
        busiest = daily.first()

        return {
            "week_start": str(week_start),
            "week_end": str(week_end),
            "total_orders": stats["total_orders"] or 0,
            "total_revenue": stats["total_revenue"] or 0,
            "avg_daily_revenue": round((stats["total_revenue"] or 0) / 7, 2),
            "busiest_day": str(busiest["day"]) if busiest else None,
        }

    def menu_popularity_report(self) -> list[dict[str, Any]]:
        """Return menu item popularity statistics sorted by quantity sold.

        Returns:
            A list of dicts with keys ``name``, ``category``, and ``qty_sold``.
        """
        rows = (
            SessionItem.objects.values(
                "menu_item__name", "menu_item__category"
            )
            .annotate(qty_sold=Sum("qty"))
            .order_by("-qty_sold")
        )
        return [
            {
                "name": r["menu_item__name"],
                "category": r["menu_item__category"],
                "qty_sold": r["qty_sold"],
            }
            for r in rows
        ]

    def export_sales_csv(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> str:
        """Export sales records between *start_date* and *end_date* as a CSV string.

        Args:
            start_date: First date to include (inclusive).
            end_date: Last date to include (inclusive).

        Returns:
            A UTF-8 CSV string.
        """
        records = SalesRecord.objects.filter(
            closed_at__date__gte=start_date, closed_at__date__lte=end_date
        ).order_by("closed_at")

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            ["id", "table_num", "customer_name", "subtotal", "discount",
             "total", "payment_method", "closed_at"]
        )
        for r in records:
            writer.writerow(
                [r.id, r.table_num, r.customer_name, r.subtotal,
                 r.discount_amount, r.total, r.payment_method,
                 r.closed_at.strftime("%Y-%m-%d %H:%M:%S")]
            )
        return buf.getvalue()

    def export_reservations_csv(self, date: datetime.date | None = None) -> str:
        """Export reservation records for *date* (or all) as a CSV string.

        Args:
            date: The date to filter by. If None, all reservations are exported.

        Returns:
            A UTF-8 CSV string.
        """
        qs = Reservation.objects.order_by("reserved_date", "reserved_time")
        if date is not None:
            qs = qs.filter(reserved_date=date)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            ["id", "table_num", "customer_name", "customer_phone",
             "party_size", "reserved_date", "reserved_time", "status", "notes"]
        )
        for r in qs:
            writer.writerow(
                [r.id, r.table.number, r.customer_name, r.customer_phone,
                 r.party_size, r.reserved_date, r.reserved_time, r.status, r.notes]
            )
        return buf.getvalue()
