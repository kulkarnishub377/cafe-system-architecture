"""Management command to create default staff accounts."""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from cafe.models import StaffProfile


class Command(BaseCommand):
    help = 'Create default staff accounts for the cafe system'

    def handle(self, *args, **kwargs):
        accounts = [
            {
                'username': 'admin',
                'password': 'Admin@91VRS',
                'first_name': 'Admin',
                'last_name': 'Manager',
                'email': 'admin@91vrscafe.in',
                'role': StaffProfile.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'kitchen1',
                'password': 'Kitchen@91VRS',
                'first_name': 'Chef',
                'last_name': 'Kumar',
                'email': 'kitchen@91vrscafe.in',
                'role': StaffProfile.ROLE_KITCHEN,
            },
            {
                'username': 'waiter1',
                'password': 'Waiter@91VRS',
                'first_name': 'Waiter',
                'last_name': 'Singh',
                'email': 'waiter@91vrscafe.in',
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
                    self.style.SUCCESS(f"  ✅  Created '{user.username}' ({role})")
                )
            else:
                self.stdout.write(f"  ⚠️  '{user.username}' already exists, skipped.")
        self.stdout.write(self.style.SUCCESS(f'\nCreated {created} new staff account(s).'))
