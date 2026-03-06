"""
Django Admin configuration for # 91 VRS Cafe.

Provides professional list displays, inline admins, custom actions,
and organised fieldsets for every model.
"""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import (
    CafeSettings,
    CustomerVisit,
    Discount,
    KitchenOrder,
    KitchenOrderItem,
    MenuItem,
    OrderFeedback,
    Reservation,
    SalesRecord,
    SessionItem,
    StaffProfile,
    Table,
    TableSession,
)


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class SessionItemInline(admin.TabularInline):
    """Inline session items inside the TableSession admin."""

    model = SessionItem
    extra = 0
    readonly_fields = ('menu_item', 'price', 'qty', 'notes')


class KitchenOrderItemInline(admin.TabularInline):
    """Inline order items inside the KitchenOrder admin."""

    model = KitchenOrderItem
    extra = 0
    readonly_fields = ('name', 'qty', 'price', 'notes')


# ---------------------------------------------------------------------------
# Menu Item
# ---------------------------------------------------------------------------

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """Admin for the menu with quick stock and trending toggles."""

    list_display = (
        'name', 'category', 'price', 'in_stock', 'trending',
        'sort_order', 'is_veg', 'is_active',
    )
    list_editable = ('in_stock', 'trending', 'sort_order')
    list_filter = ('category', 'is_veg', 'in_stock', 'trending', 'is_active')
    search_fields = ('name', 'description', 'allergens')
    ordering = ('sort_order', 'name')
    actions = ['mark_as_trending', 'mark_as_not_trending', 'mark_out_of_stock']
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'category', 'price', 'emoji', 'image')}),
        ('Properties', {'fields': ('is_veg', 'in_stock', 'trending', 'is_active', 'sort_order')}),
        ('Details', {'fields': ('description', 'calories', 'allergens', 'serving_size', 'preparation_time_minutes')}),
    )

    @admin.action(description='Mark selected items as Trending')
    def mark_as_trending(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Set trending=True on the selected menu items."""
        updated = queryset.update(trending=True)
        self.message_user(request, f'{updated} items marked as trending.')

    @admin.action(description='Remove Trending from selected items')
    def mark_as_not_trending(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Clear trending flag on the selected menu items."""
        updated = queryset.update(trending=False)
        self.message_user(request, f'{updated} items removed from trending.')

    @admin.action(description='Mark selected items as Out of Stock')
    def mark_out_of_stock(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Set in_stock=False on the selected menu items."""
        updated = queryset.update(in_stock=False)
        self.message_user(request, f'{updated} items marked as out of stock.')


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    """Admin for dining tables with quick status editing."""

    list_display = ('number', 'capacity', 'location', 'status', 'is_active')
    list_editable = ('status',)
    list_filter = ('status', 'location', 'is_active')
    search_fields = ('number', 'location')
    ordering = ('number',)


# ---------------------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------------------

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin for reservations with date hierarchy and lifecycle actions."""

    list_display = (
        'id', 'customer_name', 'customer_phone', 'table',
        'party_size', 'reserved_date', 'reserved_time', 'status',
    )
    list_filter = ('status', 'reserved_date')
    search_fields = ('customer_name', 'customer_phone')
    date_hierarchy = 'reserved_date'
    ordering = ('reserved_date', 'reserved_time')
    actions = ['confirm_reservations', 'cancel_reservations']

    @admin.action(description='Confirm selected reservations')
    def confirm_reservations(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Move selected reservations to confirmed status."""
        updated = queryset.update(status=Reservation.STATUS_CONFIRMED)
        self.message_user(request, f'{updated} reservations confirmed.')

    @admin.action(description='Cancel selected reservations')
    def cancel_reservations(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Move selected reservations to cancelled status."""
        updated = queryset.update(status=Reservation.STATUS_CANCELLED)
        self.message_user(request, f'{updated} reservations cancelled.')


# ---------------------------------------------------------------------------
# Table Sessions
# ---------------------------------------------------------------------------

@admin.register(TableSession)
class TableSessionAdmin(admin.ModelAdmin):
    """Admin for active table sessions with inline session items."""

    list_display = (
        'table_num', 'customer_name', 'session_type',
        'bill_printed', 'start_time', 'discount_code',
    )
    list_filter = ('session_type', 'bill_printed')
    search_fields = ('table_num', 'customer_name')
    inlines = [SessionItemInline]
    readonly_fields = ('start_time', 'created_at', 'updated_at')


# ---------------------------------------------------------------------------
# Kitchen Orders
# ---------------------------------------------------------------------------

@admin.register(KitchenOrder)
class KitchenOrderAdmin(admin.ModelAdmin):
    """Admin for kitchen tickets with priority filtering and bulk-complete action."""

    list_display = (
        'id', 'table_num', 'customer_name', 'status',
        'priority', 'estimated_minutes', 'created_at', 'completed_at',
    )
    list_filter = ('status', 'priority')
    search_fields = ('table_num', 'customer_name')
    date_hierarchy = 'created_at'
    ordering = ('created_at',)
    inlines = [KitchenOrderItemInline]
    readonly_fields = ('created_at', 'completed_at', 'updated_at')
    actions = ['mark_all_completed']

    @admin.action(description='Mark selected orders as Completed')
    def mark_all_completed(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Set status=completed and record completed_at for selected orders."""
        from django.utils import timezone
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} orders marked as completed.')


# ---------------------------------------------------------------------------
# Sales Records
# ---------------------------------------------------------------------------

@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    """Read-only admin for archived sales records."""

    list_display = (
        'id', 'table_num', 'customer_name', 'subtotal',
        'discount_amount', 'total', 'payment_method', 'closed_at',
    )
    list_filter = ('payment_method',)
    search_fields = ('table_num', 'customer_name')
    date_hierarchy = 'closed_at'
    readonly_fields = (
        'table_num', 'customer_name', 'special_instructions', 'items_json',
        'subtotal', 'discount_amount', 'total', 'payment_method',
        'start_time', 'closed_at', 'created_at', 'updated_at',
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Sales records are created by the system; block manual creation."""
        return False

    def tax_amount(self, obj: SalesRecord) -> int:
        """Computed tax: total − (subtotal − discount)."""
        return obj.total - (obj.subtotal - obj.discount_amount)
    tax_amount.short_description = 'Tax (₹)'


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

@admin.register(OrderFeedback)
class OrderFeedbackAdmin(admin.ModelAdmin):
    """Admin for customer feedback with rating filters."""

    list_display = (
        'id', 'table_num', 'overall_rating', 'food_rating',
        'service_rating', 'would_recommend', 'created_at',
    )
    list_filter = ('overall_rating', 'would_recommend')
    search_fields = ('table_num', 'comment')
    readonly_fields = ('created_at', 'updated_at')


# ---------------------------------------------------------------------------
# Discounts
# ---------------------------------------------------------------------------

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    """Admin for promotional discount codes."""

    list_display = (
        'code', 'discount_type', 'value', 'min_order_amount',
        'used_count', 'max_uses', 'valid_from', 'valid_until', 'is_active',
    )
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'description')
    ordering = ('-valid_until',)


# ---------------------------------------------------------------------------
# Cafe Settings (singleton)
# ---------------------------------------------------------------------------

@admin.register(CafeSettings)
class CafeSettingsAdmin(admin.ModelAdmin):
    """Admin for the cafe singleton settings with organised fieldsets."""

    fieldsets = (
        ('Identity', {
            'fields': ('cafe_name', 'phone', 'address', 'gst'),
        }),
        ('Financial', {
            'fields': ('tax_rate', 'currency_symbol', 'upi_id'),
        }),
        ('Operations', {
            'fields': ('total_tables', 'opening_time', 'closing_time'),
        }),
        ('Branding', {
            'fields': ('footer_message', 'instagram_url'),
        }),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Enforce singleton — block creation if a settings row already exists."""
        return not CafeSettings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        """Prevent accidental deletion of the settings row."""
        return False


# ---------------------------------------------------------------------------
# Staff Profiles
# ---------------------------------------------------------------------------

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    """Admin for staff user profiles."""

    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)
    raw_id_fields = ('user',)


# ---------------------------------------------------------------------------
# Customer Visits
# ---------------------------------------------------------------------------

@admin.register(CustomerVisit)
class CustomerVisitAdmin(admin.ModelAdmin):
    """Admin for anonymous customer visit records."""

    list_display = ('ip_address', 'table_num', 'sales_record', 'created_at')
    list_filter = ('table_num',)
    search_fields = ('ip_address',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
