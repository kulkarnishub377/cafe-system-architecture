"""
Serializers for # 91 VRS Cafe API.

Naming convention:
  *Serializer      – read serializer (GET responses)
  *WriteSerializer – write serializer (POST/PATCH request bodies)
  *CreateSerializer – create-only serializer
"""

from rest_framework import serializers

from .models import (
    CafeSettings,
    Discount,
    KitchenOrder,
    KitchenOrderItem,
    MenuItem,
    OrderFeedback,
    Reservation,
    SalesRecord,
    SessionItem,
    Table,
    TableSession,
)


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

class MenuItemSerializer(serializers.ModelSerializer):
    """Full read representation of a menu item, including availability flag."""

    is_available = serializers.SerializerMethodField(
        help_text='True when the item is both in_stock and is_active.'
    )

    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'price', 'category', 'image', 'emoji',
            'is_veg', 'in_stock', 'trending', 'description', 'calories',
            'preparation_time_minutes', 'allergens', 'serving_size',
            'sort_order', 'is_available', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_available']

    def get_is_available(self, obj: MenuItem) -> bool:
        """Return True only if the item is both in stock and not soft-deleted."""
        return obj.in_stock and obj.is_active


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class TableSerializer(serializers.ModelSerializer):
    """Full representation of a dining table, including its current session if occupied."""

    active_session_table_num = serializers.SerializerMethodField(
        help_text='table_num of the active session, or null.',
    )

    class Meta:
        model = Table
        fields = [
            'id', 'number', 'capacity', 'location', 'status',
            'qr_code_url', 'active_session_table_num', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'active_session_table_num']

    def get_active_session_table_num(self, obj: Table) -> int | None:
        """Return the table_num if there is an active session on this table."""
        session = TableSession.objects.filter(table_num=obj.number).first()
        return session.table_num if session else None


# ---------------------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------------------

class ReservationSerializer(serializers.ModelSerializer):
    """Read representation of a reservation, with table details embedded."""

    table_number = serializers.IntegerField(source='table.number', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'table', 'table_number', 'customer_name', 'customer_phone',
            'party_size', 'reserved_date', 'reserved_time', 'notes', 'status',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'table_number']


class ReservationCreateSerializer(serializers.ModelSerializer):
    """Write serializer for creating or updating a reservation."""

    class Meta:
        model = Reservation
        fields = [
            'table', 'customer_name', 'customer_phone', 'party_size',
            'reserved_date', 'reserved_time', 'notes', 'status',
        ]

    def validate(self, attrs):
        """Ensure no overlapping confirmed/pending reservation exists for the same table+date+time."""
        from .exceptions import ReservationConflict

        table = attrs.get('table')
        reserved_date = attrs.get('reserved_date')
        reserved_time = attrs.get('reserved_time')

        if table and reserved_date and reserved_time:
            conflict_qs = Reservation.objects.filter(
                table=table,
                reserved_date=reserved_date,
                reserved_time=reserved_time,
                status__in=[Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED],
            )
            # Exclude current instance on updates
            instance = self.instance
            if instance:
                conflict_qs = conflict_qs.exclude(pk=instance.pk)

            if conflict_qs.exists():
                raise ReservationConflict()
        return attrs


# ---------------------------------------------------------------------------
# Table Sessions
# ---------------------------------------------------------------------------

class SessionItemSerializer(serializers.ModelSerializer):
    """Flattened read representation of a session line item."""

    id = serializers.IntegerField(source='menu_item.id', read_only=True)
    name = serializers.CharField(source='menu_item.name', read_only=True)
    emoji = serializers.CharField(source='menu_item.emoji', read_only=True)
    category = serializers.CharField(source='menu_item.category', read_only=True)
    is_veg = serializers.BooleanField(source='menu_item.is_veg', read_only=True)

    class Meta:
        model = SessionItem
        fields = ['id', 'name', 'emoji', 'category', 'is_veg', 'price', 'qty', 'notes']


class SessionItemWriteSerializer(serializers.Serializer):
    """Accepts ``{id, qty}`` pairs when adding items to a session."""

    id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(max_length=200, required=False, default='')


class BillBreakdownSerializer(serializers.Serializer):
    """Read-only serializer for the detailed bill breakdown returned by generate_bill."""

    subtotal = serializers.IntegerField()
    discount = serializers.IntegerField()
    tax = serializers.IntegerField()
    total = serializers.IntegerField()
    tax_rate = serializers.FloatField()
    discount_code = serializers.CharField(allow_blank=True)


class TableSessionSerializer(serializers.ModelSerializer):
    """Full read representation of a table session with items and bill total."""

    items = SessionItemSerializer(source='session_items', many=True, read_only=True)
    total = serializers.SerializerMethodField(help_text='Grand total after discount + tax.')

    class Meta:
        model = TableSession
        fields = [
            'table_num', 'customer_name', 'special_instructions',
            'session_type', 'discount_code', 'discount_amount',
            'start_time', 'bill_printed', 'items', 'total',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['start_time', 'created_at', 'updated_at', 'total']

    def get_total(self, obj: TableSession) -> int:
        """Return grand total including tax, after discount."""
        return obj.total()


# ---------------------------------------------------------------------------
# Kitchen Orders
# ---------------------------------------------------------------------------

class KitchenOrderItemSerializer(serializers.ModelSerializer):
    """Line item within a kitchen order."""

    class Meta:
        model = KitchenOrderItem
        fields = ['id', 'name', 'qty', 'price', 'notes']


class KitchenOrderSerializer(serializers.ModelSerializer):
    """Full read representation of a kitchen order ticket."""

    items = KitchenOrderItemSerializer(source='order_items', many=True, read_only=True)

    class Meta:
        model = KitchenOrder
        fields = [
            'id', 'table_num', 'customer_name', 'special_instructions',
            'status', 'priority', 'estimated_minutes', 'notes',
            'created_at', 'completed_at', 'items',
        ]
        read_only_fields = ['created_at', 'completed_at', 'estimated_minutes']


# ---------------------------------------------------------------------------
# Sales Records
# ---------------------------------------------------------------------------

class SalesRecordSerializer(serializers.ModelSerializer):
    """Full read representation of a completed/archived sales record."""

    class Meta:
        model = SalesRecord
        fields = [
            'id', 'table_num', 'customer_name', 'special_instructions',
            'items_json', 'subtotal', 'discount_amount', 'total',
            'payment_method', 'start_time', 'closed_at',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['closed_at', 'created_at', 'updated_at']


# ---------------------------------------------------------------------------
# Order Feedback
# ---------------------------------------------------------------------------

class OrderFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for customer feedback on a completed session."""

    class Meta:
        model = OrderFeedback
        fields = [
            'id', 'session_record', 'table_num', 'overall_rating',
            'food_rating', 'service_rating', 'comment', 'would_recommend',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_overall_rating(self, value: int) -> int:
        """Ensure overall_rating is between 1 and 5."""
        if not (1 <= value <= 5):
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value

    def validate(self, attrs):
        """Validate optional ratings are 1–5."""
        for field in ('food_rating', 'service_rating'):
            value = attrs.get(field)
            if value is not None and not (1 <= value <= 5):
                raise serializers.ValidationError({field: 'Rating must be between 1 and 5.'})
        return attrs


# ---------------------------------------------------------------------------
# Discounts
# ---------------------------------------------------------------------------

class DiscountSerializer(serializers.ModelSerializer):
    """Full read/write serializer for discount codes."""

    is_valid_now = serializers.SerializerMethodField(
        help_text='Whether this discount is currently valid.',
    )

    class Meta:
        model = Discount
        fields = [
            'id', 'code', 'description', 'discount_type', 'value',
            'min_order_amount', 'max_uses', 'used_count',
            'valid_from', 'valid_until', 'is_valid_now',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['used_count', 'created_at', 'updated_at', 'is_valid_now']

    def get_is_valid_now(self, obj: Discount) -> bool:
        """Return True if the discount is currently active and usable."""
        return obj.is_valid()


class DiscountValidateSerializer(serializers.Serializer):
    """Request body for validating a discount code against an order subtotal."""

    code = serializers.CharField(max_length=50)
    subtotal = serializers.IntegerField(min_value=0)


# ---------------------------------------------------------------------------
# Cafe Settings
# ---------------------------------------------------------------------------

class CafeSettingsSerializer(serializers.ModelSerializer):
    """Serializer for the cafe-wide singleton settings."""

    class Meta:
        model = CafeSettings
        fields = [
            'cafe_name', 'phone', 'address', 'gst', 'tax_rate', 'total_tables',
            'opening_time', 'closing_time', 'currency_symbol',
            'footer_message', 'upi_id', 'instagram_url',
        ]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class DailyStatsSerializer(serializers.Serializer):
    """Serializer for the daily overview stats endpoint."""

    revenue = serializers.IntegerField()
    orders = serializers.IntegerField()
    avg_order = serializers.IntegerField()
    active_tables = serializers.IntegerField()
    feedback_avg = serializers.FloatField(allow_null=True)
