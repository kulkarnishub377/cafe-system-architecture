from django.db import models


class MenuItem(models.Model):
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

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} (₹{self.price})'


class TableSession(models.Model):
    """An active dine-in session for a specific table."""

    table_num = models.PositiveSmallIntegerField(unique=True)
    customer_name = models.CharField(max_length=200, blank=True)
    special_instructions = models.TextField(blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    bill_printed = models.BooleanField(default=False)

    class Meta:
        ordering = ['table_num']

    def __str__(self):
        return f'Table {self.table_num}'

    def total(self):
        subtotal = sum(item.price * item.qty for item in self.session_items.all())
        from cafe.models import CafeSettings  # noqa: avoid circular at module level
        settings = CafeSettings.get_settings()
        return round(subtotal * (1 + settings.tax_rate / 100))


class SessionItem(models.Model):
    """A line item inside a TableSession (cart)."""

    session = models.ForeignKey(
        TableSession, on_delete=models.CASCADE, related_name='session_items'
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    qty = models.PositiveSmallIntegerField(default=1)

    # Snapshot of price at order time
    price = models.PositiveIntegerField()

    class Meta:
        unique_together = ('session', 'menu_item')

    def __str__(self):
        return f'{self.qty}x {self.menu_item.name} @ Table {self.session.table_num}'


class KitchenOrder(models.Model):
    """An order ticket sent to the kitchen."""

    STATUS_PENDING = 'pending'
    STATUS_PREPARING = 'preparing'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    table_num = models.PositiveSmallIntegerField()
    customer_name = models.CharField(max_length=200, blank=True)
    special_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Order #{self.pk} – Table {self.table_num} ({self.status})'


class KitchenOrderItem(models.Model):
    """A line item within a KitchenOrder."""

    order = models.ForeignKey(
        KitchenOrder, on_delete=models.CASCADE, related_name='order_items'
    )
    name = models.CharField(max_length=200)
    qty = models.PositiveSmallIntegerField(default=1)
    price = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.qty}x {self.name}'


class SalesRecord(models.Model):
    """Archived record of a closed table session."""

    table_num = models.PositiveSmallIntegerField()
    customer_name = models.CharField(max_length=200, blank=True)
    special_instructions = models.TextField(blank=True)
    items_json = models.JSONField(default=list)
    subtotal = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    start_time = models.DateTimeField()
    closed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-closed_at']

    def __str__(self):
        return f'Sale #{self.pk} – Table {self.table_num} (₹{self.total})'


class CafeSettings(models.Model):
    """Singleton model for cafe-wide configuration."""

    cafe_name = models.CharField(max_length=200, default='# 91 VRS Cafe')
    phone = models.CharField(max_length=30, default='+91 98765 43210')
    address = models.CharField(max_length=300, default='123 Coffee Street, Bengaluru')
    gst = models.CharField(max_length=30, default='29XXXXX1234X1ZX')
    tax_rate = models.FloatField(default=5.0, help_text='Tax percentage applied to bills')
    total_tables = models.PositiveSmallIntegerField(default=12)

    class Meta:
        verbose_name_plural = 'Cafe Settings'

    def __str__(self):
        return self.cafe_name

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

