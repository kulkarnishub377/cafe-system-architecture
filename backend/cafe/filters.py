"""
django-filter FilterSet classes for # 91 VRS Cafe API endpoints.

Each FilterSet maps request query params to ORM lookups cleanly,
keeping all filter logic out of the view layer.
"""

import django_filters

from .models import KitchenOrder, MenuItem, Reservation, SalesRecord


class MenuItemFilter(django_filters.FilterSet):
    """Filter menu items by category, dietary flags, stock status, and price range."""

    category = django_filters.CharFilter(method='filter_category')
    price__gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price__lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = MenuItem
        fields = {
            'is_veg': ['exact'],
            'in_stock': ['exact'],
            'trending': ['exact'],
        }

    def filter_category(self, queryset, name, value):
        """
        Handle the special ``category=trending`` shorthand in addition to real categories.
        Passing ``trending`` as the category filters by the ``trending=True`` flag.
        """
        if value == 'trending':
            return queryset.filter(trending=True)
        return queryset.filter(category=value)


class KitchenOrderFilter(django_filters.FilterSet):
    """Filter kitchen orders by status, priority, table, and creation date."""

    created_at__date = django_filters.DateFilter(field_name='created_at', lookup_expr='date')

    class Meta:
        model = KitchenOrder
        fields = {
            'status': ['exact'],
            'priority': ['exact'],
            'table_num': ['exact'],
        }


class SalesRecordFilter(django_filters.FilterSet):
    """Filter sales records by table, payment method, and closed date range."""

    closed_at__date__gte = django_filters.DateFilter(field_name='closed_at', lookup_expr='date__gte')
    closed_at__date__lte = django_filters.DateFilter(field_name='closed_at', lookup_expr='date__lte')

    class Meta:
        model = SalesRecord
        fields = {
            'table_num': ['exact'],
            'payment_method': ['exact'],
        }


class ReservationFilter(django_filters.FilterSet):
    """Filter reservations by status, date, and table number."""

    class Meta:
        model = Reservation
        fields = {
            'status': ['exact'],
            'reserved_date': ['exact'],
            'table__number': ['exact'],
        }
