"""
Management command: create_staff_token

Usage:
    python manage.py create_staff_token <username> [--role admin|kitchen|cashier]
                                                    [--password <pw>] [--create]

Creates (or fetches) a DRF Token for a staff user and prints it.
Use --create to create the user if they don't exist yet.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token

from cafe.models import StaffProfile


class Command(BaseCommand):
    help = 'Create or fetch an auth token for a staff user.'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Django username')
        parser.add_argument(
            '--role',
            type=str,
            default=StaffProfile.ROLE_KITCHEN,
            choices=[StaffProfile.ROLE_ADMIN, StaffProfile.ROLE_KITCHEN, StaffProfile.ROLE_WAITER],
            help='Staff role (default: kitchen)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='changeme123',
            help='Password for new user (only used with --create)',
        )
        parser.add_argument(
            '--create',
            action='store_true',
            help='Create the user if they do not exist',
        )

    def handle(self, *args, **options):
        username = options['username']
        role = options['role']
        password = options['password']
        should_create = options['create']

        if should_create:
            user, user_created = User.objects.get_or_create(username=username)
            if user_created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
            else:
                self.stdout.write(f'User already exists: {username}')
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(
                    f'User "{username}" does not exist. Use --create to create them.'
                )

        profile, profile_created = StaffProfile.objects.get_or_create(
            user=user, defaults={'role': role},
        )
        if profile_created:
            self.stdout.write(f'Created StaffProfile with role: {role}')
        else:
            self.stdout.write(f'Existing StaffProfile role: {profile.role}')

        token, token_created = Token.objects.get_or_create(user=user)
        action = 'Created' if token_created else 'Existing'
        self.stdout.write(
            self.style.SUCCESS(f'{action} token for {username} ({profile.role}): {token.key}')
        )
