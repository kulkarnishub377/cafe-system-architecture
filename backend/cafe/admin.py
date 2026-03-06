from django.contrib import admin

from .models import (
    CafeSettings,
    KitchenOrder,
    KitchenOrderItem,
    MenuItem,
    SalesRecord,
    SessionItem,
    TableSession,
)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_veg', 'in_stock', 'trending')
    list_filter = ('category', 'is_veg', 'in_stock', 'trending')
    search_fields = ('name', 'description')
    list_editable = ('in_stock', 'trending')


class SessionItemInline(admin.TabularInline):
    model = SessionItem
    extra = 0
    readonly_fields = ('menu_item', 'price', 'qty')


@admin.register(TableSession)
class TableSessionAdmin(admin.ModelAdmin):
    list_display = ('table_num', 'customer_name', 'start_time', 'bill_printed')
    inlines = [SessionItemInline]


class KitchenOrderItemInline(admin.TabularInline):
    model = KitchenOrderItem
    extra = 0


@admin.register(KitchenOrder)
class KitchenOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_num', 'customer_name', 'status', 'created_at')
    list_filter = ('status',)
    inlines = [KitchenOrderItemInline]


@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_num', 'customer_name', 'total', 'closed_at')
    readonly_fields = ('items_json', 'start_time', 'closed_at', 'subtotal', 'total')


@admin.register(CafeSettings)
class CafeSettingsAdmin(admin.ModelAdmin):
    list_display = ('cafe_name', 'phone', 'tax_rate', 'total_tables')

    def has_add_permission(self, request):
        # Only allow one settings record
        return not CafeSettings.objects.exists()

