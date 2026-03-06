"""
Models for # SK cafe.

Hierarchy:
  BaseModel (abstract) → all domain models
  MenuItem, Table, Reservation, TableSession, SessionItem,
  KitchenOrder, KitchenOrderItem, Discount, OrderFeedback,
  SalesRecord, CafeSettings
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BaseModel(models.Model):
    """Abstract base that stamps every record with audit timestamps and soft-delete flag."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

class MenuItem(BaseModel):
    """Represents a single item on the cafe menu."""

    CATEGORY_CHOICES = [
        ('coffee', 'Coffee'),
        ('burgers', 'Burgers'),
        ('pizza', 'Pizza'),
        ('mains', 'Mains'),
        ('desserts', 'Desserts'),
        ('drinks', 'Drinks'),
        ('snacks', 'Snacks'),
    ]

    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField(help_text='Price in INR (₹)')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.URLField(max_length=500, blank=True)
    emoji = models.CharField(max_length=10, default='🍽️')
    is_veg = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    trending = models.BooleanField(default=False)
    description = models.CharField(max_length=300, blank=True)
    calories = models.PositiveIntegerField(null=True, blank=True)
    preparation_time_minutes = models.PositiveSmallIntegerField(default=10)
    allergens = models.CharField(
        max_length=300, blank=True,
        help_text='Comma-separated list, e.g. "gluten, dairy"',
    )
    serving_size = models.CharField(
        max_length=100, blank=True,
        help_text='e.g. "300ml" or "250g"',
    )
    sort_order = models.PositiveSmallIntegerField(
        default=0, help_text='Lower values appear first in listings',
    )

    class Meta:
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['in_stock']),
            models.Index(fields=['trending']),
        ]

    def __str__(self) -> str:
        return f'{self.name} (₹{self.price})'


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class Table(BaseModel):
    """A physical dining table inside the cafe."""

    STATUS_AVAILABLE = 'available'
    STATUS_OCCUPIED = 'occupied'
    STATUS_RESERVED = 'reserved'
    STATUS_MAINTENANCE = 'maintenance'

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_OCCUPIED, 'Occupied'),
        (STATUS_RESERVED, 'Reserved'),
        (STATUS_MAINTENANCE, 'Maintenance'),
    ]

    number = models.PositiveSmallIntegerField(unique=True, help_text='Table number shown to customers')
    capacity = models.PositiveSmallIntegerField(default=4)
    location = models.CharField(
        max_length=100, blank=True,
        help_text='e.g. "Window", "Terrace", "Main Hall"',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    qr_code_url = models.CharField(max_length=500, blank=True, help_text='URL to the table QR code image')
    qr_code_data = models.TextField(
        blank=True,
        help_text='Base64-encoded PNG of the QR code (data URI ready for <img src>)',
    )

    class Meta:
        ordering = ['number']

    def __str__(self) -> str:
        return f'Table {self.number} ({self.status})'


# ---------------------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------------------

class Reservation(BaseModel):
    """A table reservation made by a customer in advance."""

    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_SEATED = 'seated'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_SEATED, 'Seated'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    table = models.ForeignKey(Table, on_delete=models.PROTECT, related_name='reservations')
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    party_size = models.PositiveSmallIntegerField()
    reserved_date = models.DateField()
    reserved_time = models.TimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        ordering = ['reserved_date', 'reserved_time']
        indexes = [
            models.Index(fields=['reserved_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:
        return (
            f'Reservation #{self.pk} – {self.customer_name} '
            f'@ Table {self.table.number} on {self.reserved_date}'
        )


# ---------------------------------------------------------------------------
# Table Sessions (active orders)
# ---------------------------------------------------------------------------

class TableSession(BaseModel):
    """An active dine-in session for a specific table."""

    SESSION_TYPE_DINE_IN = 'dine_in'
    SESSION_TYPE_TAKEAWAY = 'takeaway'
    SESSION_TYPE_DELIVERY = 'delivery'

    SESSION_TYPE_CHOICES = [
        (SESSION_TYPE_DINE_IN, 'Dine-In'),
        (SESSION_TYPE_TAKEAWAY, 'Takeaway'),
        (SESSION_TYPE_DELIVERY, 'Delivery'),
    ]

    table_num = models.PositiveSmallIntegerField(unique=True)
    customer_name = models.CharField(max_length=200, blank=True)
    special_instructions = models.TextField(blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    bill_printed = models.BooleanField(default=False)
    session_type = models.CharField(
        max_length=20, choices=SESSION_TYPE_CHOICES, default=SESSION_TYPE_DINE_IN,
    )
    discount_code = models.CharField(max_length=50, blank=True)
    discount_amount = models.PositiveIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text='Customer IP for anonymous tracking')

    class Meta:
        ordering = ['table_num']
        indexes = [
            models.Index(fields=['table_num']),
        ]

    def __str__(self) -> str:
        return f'Table {self.table_num} ({self.session_type})'

    def total(self) -> int:
        """Return grand total including tax but after discount."""
        from cafe.models import CafeSettings  # avoid circular at module level
        subtotal = sum(item.price * item.qty for item in self.session_items.all())
        settings = CafeSettings.get_settings()
        taxable = max(0, subtotal - self.discount_amount)
        return round(taxable * (1 + settings.tax_rate / 100))


class SessionItem(BaseModel):
    """A line item inside a TableSession (cart entry)."""

    session = models.ForeignKey(
        TableSession, on_delete=models.CASCADE, related_name='session_items',
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    qty = models.PositiveSmallIntegerField(default=1)
    price = models.PositiveIntegerField(help_text='Price snapshot at order time')
    notes = models.CharField(max_length=200, blank=True, help_text='Item-level special request')

    class Meta:
        unique_together = ('session', 'menu_item')

    def __str__(self) -> str:
        return f'{self.qty}× {self.menu_item.name} @ Table {self.session.table_num}'


# ---------------------------------------------------------------------------
# Kitchen Orders
# ---------------------------------------------------------------------------

class KitchenOrder(BaseModel):
    """An order ticket sent to the kitchen."""

    STATUS_PENDING = 'pending'
    STATUS_PREPARING = 'preparing'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    PRIORITY_NORMAL = 'normal'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'

    PRIORITY_CHOICES = [
        (PRIORITY_NORMAL, 'Normal'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    ]

    table_num = models.PositiveSmallIntegerField()
    customer_name = models.CharField(max_length=200, blank=True)
    special_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    estimated_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return f'Order #{self.pk} – Table {self.table_num} ({self.status})'


class KitchenOrderItem(models.Model):
    """A line item within a KitchenOrder."""

    order = models.ForeignKey(
        KitchenOrder, on_delete=models.CASCADE, related_name='order_items',
    )
    name = models.CharField(max_length=200)
    qty = models.PositiveSmallIntegerField(default=1)
    price = models.PositiveIntegerField()
    notes = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return f'{self.qty}× {self.name}'


# ---------------------------------------------------------------------------
# Discounts
# ---------------------------------------------------------------------------

class Discount(BaseModel):
    """A promotional discount code that can be applied to orders."""

    DISCOUNT_TYPE_PERCENTAGE = 'percentage'
    DISCOUNT_TYPE_FIXED = 'fixed'

    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_TYPE_PERCENTAGE, 'Percentage'),
        (DISCOUNT_TYPE_FIXED, 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True, help_text='Promo code entered by customer')
    description = models.CharField(max_length=300, blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(
        max_digits=8, decimal_places=2,
        help_text='Percentage (0-100) or fixed INR amount',
    )
    min_order_amount = models.PositiveIntegerField(
        default=0, help_text='Minimum subtotal required for the code to apply',
    )
    max_uses = models.PositiveIntegerField(
        null=True, blank=True, help_text='Leave blank for unlimited uses',
    )
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateField()
    valid_until = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['valid_until']),
        ]

    def __str__(self) -> str:
        return f'{self.code} ({self.discount_type}: {self.value})'

    def is_valid(self) -> bool:
        """Return True if the discount is active, within date range, and not exhausted."""
        if not self.is_active:
            return False
        today = timezone.localdate()
        if not (self.valid_from <= today <= self.valid_until):
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True

    def calculate_discount(self, subtotal: int) -> int:
        """Return the discount amount (in INR) to deduct from *subtotal*."""
        if subtotal < self.min_order_amount:
            return 0
        if self.discount_type == self.DISCOUNT_TYPE_PERCENTAGE:
            return round(subtotal * float(self.value) / 100)
        return min(int(self.value), subtotal)


# ---------------------------------------------------------------------------
# Sales Records
# ---------------------------------------------------------------------------

class SalesRecord(BaseModel):
    """Archived record of a closed table session."""

    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_UPI = 'upi'

    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Cash'),
        (PAYMENT_CARD, 'Card'),
        (PAYMENT_UPI, 'UPI'),
    ]

    table_num = models.PositiveSmallIntegerField()
    customer_name = models.CharField(max_length=200, blank=True)
    special_instructions = models.TextField(blank=True)
    items_json = models.JSONField(default=list)
    subtotal = models.PositiveIntegerField(default=0)
    discount_amount = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    start_time = models.DateTimeField()
    closed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text='Customer IP captured at order time')

    class Meta:
        ordering = ['-closed_at']
        indexes = [
            models.Index(fields=['closed_at']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self) -> str:
        return f'Sale #{self.pk} – Table {self.table_num} (₹{self.total})'


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class OrderFeedback(BaseModel):
    """Customer feedback submitted after a session is closed."""

    session_record = models.ForeignKey(
        SalesRecord, on_delete=models.PROTECT, related_name='feedbacks',
    )
    table_num = models.PositiveSmallIntegerField()
    overall_rating = models.PositiveSmallIntegerField(help_text='1–5 stars')
    food_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    service_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    would_recommend = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Feedback #{self.pk} – Table {self.table_num} ({self.overall_rating}★)'

    def clean(self) -> None:
        """Validate that all supplied ratings are in the 1–5 range."""
        for field in ('overall_rating', 'food_rating', 'service_rating'):
            value = getattr(self, field)
            if value is not None and not (1 <= value <= 5):
                raise ValidationError({field: 'Rating must be between 1 and 5.'})


# ---------------------------------------------------------------------------
# Cafe Settings (singleton)
# ---------------------------------------------------------------------------

class CafeSettings(models.Model):
    """Singleton model for cafe-wide configuration (always pk=1)."""

    cafe_name = models.CharField(max_length=200, default='# SK cafe')
    phone = models.CharField(max_length=30, default='+91 98765 43210')
    address = models.CharField(max_length=300, default='123 Coffee Street, Bengaluru')
    gst = models.CharField(max_length=30, default='29XXXXX1234X1ZX')
    tax_rate = models.FloatField(default=5.0, help_text='Tax percentage applied to bills')
    total_tables = models.PositiveSmallIntegerField(default=12)
    opening_time = models.TimeField(default='09:00')
    closing_time = models.TimeField(default='23:00')
    currency_symbol = models.CharField(max_length=5, default='₹')
    footer_message = models.CharField(
        max_length=300, default='Thank you for visiting # SK cafe!',
    )
    upi_id = models.CharField(max_length=100, blank=True)
    instagram_url = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = 'Cafe Settings'

    def __str__(self) -> str:
        return self.cafe_name

    @classmethod
    def get_settings(cls) -> 'CafeSettings':
        """Return the singleton settings object, creating it if necessary."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ---------------------------------------------------------------------------
# Staff Profiles
# ---------------------------------------------------------------------------

class StaffProfile(models.Model):
    """Extended profile for cafe staff members linked to Django's User model."""

    ROLE_ADMIN = 'admin'
    ROLE_KITCHEN = 'kitchen'
    ROLE_WAITER = 'waiter'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin / Manager'),
        (ROLE_KITCHEN, 'Kitchen Staff'),
        (ROLE_WAITER, 'Waiter / Front-of-house'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_WAITER)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture_url = models.URLField(max_length=500, blank=True)
    is_on_duty = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Staff Profile'

    def __str__(self) -> str:
        return f'{self.user.get_full_name() or self.user.username} ({self.role})'


# ---------------------------------------------------------------------------
# Customer Visits
# ---------------------------------------------------------------------------

class CustomerVisit(models.Model):
    """
    Tracks anonymous customer visits by IP address.
    Customers do not have accounts – we identify them by IP only.
    """
    ip_address = models.GenericIPAddressField(unique=True)
    preferred_name = models.CharField(max_length=200, blank=True, help_text='Name set by customer on last order')
    visit_count = models.PositiveIntegerField(default=1)
    first_visit = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    device_info = models.CharField(max_length=500, blank=True, help_text='User-Agent string of last visit')

    class Meta:
        ordering = ['-last_seen']
        indexes = [models.Index(fields=['ip_address'])]
        verbose_name = 'Customer Visit'

    def __str__(self) -> str:
        return f'Customer @ {self.ip_address} (visits: {self.visit_count})'
