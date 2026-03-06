from rest_framework import serializers

from .models import (
    CafeSettings,
    KitchenOrder,
    KitchenOrderItem,
    MenuItem,
    SalesRecord,
    SessionItem,
    TableSession,
)


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'


# ---------------------------------------------------------------------------
# Table Sessions
# ---------------------------------------------------------------------------

class SessionItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='menu_item.id', read_only=True)
    name = serializers.CharField(source='menu_item.name', read_only=True)
    emoji = serializers.CharField(source='menu_item.emoji', read_only=True)
    category = serializers.CharField(source='menu_item.category', read_only=True)
    is_veg = serializers.BooleanField(source='menu_item.is_veg', read_only=True)

    class Meta:
        model = SessionItem
        fields = ['id', 'name', 'emoji', 'category', 'is_veg', 'price', 'qty']


class SessionItemWriteSerializer(serializers.Serializer):
    """Accepts {id, qty} pairs when adding items to a session."""
    id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1)


class TableSessionSerializer(serializers.ModelSerializer):
    items = SessionItemSerializer(source='session_items', many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = TableSession
        fields = [
            'table_num', 'customer_name', 'special_instructions',
            'start_time', 'bill_printed', 'items', 'total',
        ]

    def get_total(self, obj):
        return obj.total()


# ---------------------------------------------------------------------------
# Kitchen Orders
# ---------------------------------------------------------------------------

class KitchenOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = KitchenOrderItem
        fields = ['name', 'qty', 'price']


class KitchenOrderSerializer(serializers.ModelSerializer):
    items = KitchenOrderItemSerializer(source='order_items', many=True, read_only=True)

    class Meta:
        model = KitchenOrder
        fields = [
            'id', 'table_num', 'customer_name', 'special_instructions',
            'status', 'created_at', 'completed_at', 'items',
        ]


# ---------------------------------------------------------------------------
# Sales Records
# ---------------------------------------------------------------------------

class SalesRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesRecord
        fields = '__all__'


# ---------------------------------------------------------------------------
# Cafe Settings
# ---------------------------------------------------------------------------

class CafeSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CafeSettings
        fields = ['cafe_name', 'phone', 'address', 'gst', 'tax_rate', 'total_tables']
