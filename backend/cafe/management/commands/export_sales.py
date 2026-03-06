"""Django management command: export_sales

Usage::

    python manage.py export_sales [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                  [--output /path/to/file.csv]
"""

from __future__ import annotations

import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from cafe.models import SalesRecord
from cafe.reports import ReportGenerator


class Command(BaseCommand):
    """Export sales data to CSV and print summary statistics."""

    help = "Export sales data to CSV with summary statistics."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            metavar="YYYY-MM-DD",
            default=None,
            help="Start date (inclusive). Defaults to 7 days ago.",
        )
        parser.add_argument(
            "--end",
            metavar="YYYY-MM-DD",
            default=None,
            help="End date (inclusive). Defaults to today.",
        )
        parser.add_argument(
            "--output",
            metavar="FILE",
            default=None,
            help="Path to output CSV file. If omitted, prints CSV to stdout.",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()

        try:
            start_date = (
                datetime.date.fromisoformat(options["start"])
                if options["start"]
                else today - datetime.timedelta(days=7)
            )
            end_date = (
                datetime.date.fromisoformat(options["end"])
                if options["end"]
                else today
            )
        except ValueError as exc:
            raise CommandError(f"Invalid date format: {exc}") from exc

        if start_date > end_date:
            raise CommandError("--start must not be after --end.")

        gen = ReportGenerator()
        csv_content = gen.export_sales_csv(start_date, end_date)

        output_path = options["output"]
        if output_path:
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(csv_content)
            self.stdout.write(self.style.SUCCESS(f"CSV saved to {output_path}"))
        else:
            self.stdout.write(csv_content)

        # Print summary statistics
        qs = SalesRecord.objects.filter(
            closed_at__date__gte=start_date, closed_at__date__lte=end_date
        )
        stats = qs.aggregate(
            total_orders=Count("id"),
            total_revenue=Sum("total"),
            avg_order=Avg("total"),
        )
        self.stdout.write("\n--- Summary ---")
        self.stdout.write(f"Period       : {start_date} → {end_date}")
        self.stdout.write(f"Total orders : {stats['total_orders'] or 0}")
        self.stdout.write(f"Total revenue: ₹{stats['total_revenue'] or 0}")
        self.stdout.write(
            f"Avg order    : ₹{round(float(stats['avg_order'] or 0), 2)}"
        )
