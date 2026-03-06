"""Django management command: generate_report

Usage::

    python manage.py generate_report [--type daily|weekly|menu] [--date YYYY-MM-DD]
                                     [--output /path/to/file] [--format text|csv]
"""

from __future__ import annotations

import datetime
import json

from django.core.management.base import BaseCommand, CommandError

from cafe.reports import ReportGenerator


class Command(BaseCommand):
    """Generate a cafe report and print it or save it to a file."""

    help = "Generate a cafe report (daily, weekly, or menu popularity)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            choices=["daily", "weekly", "menu"],
            default="daily",
            help="Type of report to generate (default: daily).",
        )
        parser.add_argument(
            "--date",
            metavar="YYYY-MM-DD",
            default=None,
            help="Date for daily report (default: today).",
        )
        parser.add_argument(
            "--output",
            metavar="FILE",
            default=None,
            help="Path to output file. If omitted, prints to stdout.",
        )
        parser.add_argument(
            "--format",
            choices=["text", "csv"],
            default="text",
            help="Output format: text (default) or csv.",
        )

    def handle(self, *args, **options):
        gen = ReportGenerator()
        report_type = options["type"]
        fmt = options["format"]
        output_path = options["output"]

        date = None
        if options["date"]:
            try:
                date = datetime.date.fromisoformat(options["date"])
            except ValueError as exc:
                raise CommandError(f"Invalid date format: {options['date']}") from exc

        if fmt == "csv":
            if report_type != "daily":
                raise CommandError("CSV format is only supported for the daily report type.")
            today = date or datetime.date.today()
            content = gen.export_sales_csv(today, today)
        else:
            if report_type == "daily":
                data = gen.daily_sales_report(date=date)
            elif report_type == "weekly":
                data = gen.weekly_performance_report()
            else:
                data = gen.menu_popularity_report()
            content = json.dumps(data, indent=2, default=str)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            self.stdout.write(
                self.style.SUCCESS(f"Report saved to {output_path}")
            )
        else:
            self.stdout.write(content)
