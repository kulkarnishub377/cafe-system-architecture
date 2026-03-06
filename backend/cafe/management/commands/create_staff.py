"""Management command to create default staff accounts."""
import os
import secrets
import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from cafe.models import StaffProfile


def _generate_password(length=16):
    """Return a cryptographically secure random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = 'Create default staff accounts for the cafe system'

    def handle(self, *args, **kwargs):
        admin_pw = os.environ.get('ADMIN_PASSWORD') or _generate_password()
        kitchen_pw = os.environ.get('KITCHEN1_PASSWORD') or _generate_password()
        waiter_pw = os.environ.get('WAITER1_PASSWORD') or _generate_password()
        accounts = [
            {
                'username': 'admin',
                'password': admin_pw,
                'first_name': 'Admin',
                'last_name': 'Manager',
                'email': 'admin@skcafe.in',
                'role': StaffProfile.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'kitchen1',
                'password': kitchen_pw,
                'first_name': 'Chef',
                'last_name': 'Kumar',
                'email': 'kitchen@skcafe.in',
                'role': StaffProfile.ROLE_KITCHEN,
            },
            {
                'username': 'waiter1',
                'password': waiter_pw,
                'first_name': 'Waiter',
                'last_name': 'Singh',
                'email': 'waiter@skcafe.in',
                'role': StaffProfile.ROLE_WAITER,
            },
        ]
        created = 0
        for acc in accounts:
            role = acc.pop('role')
            is_staff = acc.pop('is_staff', False)
            is_superuser = acc.pop('is_superuser', False)
            password = acc.pop('password')
            user, new = User.objects.get_or_create(
                username=acc['username'], defaults=acc
            )
            if new:
                user.set_password(password)
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.save()
                StaffProfile.objects.get_or_create(user=user, defaults={'role': role})
                created += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  ✅  Created '{user.username}' ({role})  "
                        f"password: {password}  "
                        f"⚠️  Save this password now — it will not be shown again."
                    )
                )
            else:
                self.stdout.write(f"  ⚠️  '{user.username}' already exists, skipped.")
        self.stdout.write(self.style.SUCCESS(f'\nCreated {created} new staff account(s).'))
