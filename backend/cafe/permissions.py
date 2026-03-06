"""
Custom DRF permission classes for # 91 VRS Cafe.
"""
from rest_framework.permissions import BasePermission


class IsStaffMember(BasePermission):
    """Allow access to any authenticated staff user (any role) or superuser."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'staff_profile')


class IsKitchenOrAdmin(BasePermission):
    """Allow access to kitchen staff or admin staff only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        profile = getattr(request.user, 'staff_profile', None)
        return profile is not None and profile.role in ('kitchen', 'admin')


class IsAdminStaff(BasePermission):
    """Allow access to admin staff or superuser only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        profile = getattr(request.user, 'staff_profile', None)
        return profile is not None and profile.role == 'admin'
