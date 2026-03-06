"""
Management command: seed_tables
Creates 12 dining tables in the database for SK Cafe.

Usage:
    python manage.py seed_tables          # create only (skip if exists)
    python manage.py seed_tables --reset  # wipe and recreate
"""

from django.core.management.base import BaseCommand

from cafe.models import Table

TABLE_DEFINITIONS = [
    {'number': 1, 'capacity': 2, 'location': 'Window'},
    {'number': 2, 'capacity': 2, 'location': 'Window'},
    {'number': 3, 'capacity': 4, 'location': 'Main Hall'},
    {'number': 4, 'capacity': 4, 'location': 'Main Hall'},
    {'number': 5, 'capacity': 4, 'location': 'Main Hall'},
    {'number': 6, 'capacity': 4, 'location': 'Main Hall'},
    {'number': 7, 'capacity': 6, 'location': 'Main Hall'},
    {'number': 8, 'capacity': 6, 'location': 'Main Hall'},
    {'number': 9, 'capacity': 4, 'location': 'Terrace'},
    {'number': 10, 'capacity': 4, 'location': 'Terrace'},
    {'number': 11, 'capacity': 6, 'location': 'Terrace'},
    {'number': 12, 'capacity': 8, 'location': 'Private Room'},
]


class Command(BaseCommand):
    """Seed the database with the 12 standard dining tables."""

    help = 'Seed the database with 12 dining tables for SK Cafe.'

    def add_arguments(self, parser):
        """Add optional --reset flag."""
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing tables before seeding.',
        )

    def handle(self, *args, **options):
        """Execute the command, creating tables as needed."""
        if options['reset']:
            deleted, _ = Table.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing tables.'))

        created_count = 0
        for data in TABLE_DEFINITIONS:
            _, created = Table.objects.get_or_create(
                number=data['number'],
                defaults={k: v for k, v in data.items() if k != 'number'},
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅  Seeded {created_count} new tables '
            f'({len(TABLE_DEFINITIONS) - created_count} already existed).'
        ))
