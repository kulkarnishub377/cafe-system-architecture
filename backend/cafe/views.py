"""
ViewSets for # 91 VRS Cafe API.

All ViewSets use drf-spectacular @extend_schema decorators, proper
select_related/prefetch_related for efficient querying, and return
correct HTTP status codes with descriptive error messages.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import Avg, Sum
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from .exceptions import InvalidDiscount, MenuItemOutOfStock
from .filters import KitchenOrderFilter, MenuItemFilter, ReservationFilter, SalesRecordFilter
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
from .serializers import (
    BillBreakdownSerializer,
    CafeSettingsSerializer,
    DailyStatsSerializer,
    DiscountSerializer,
    DiscountValidateSerializer,
    KitchenOrderSerializer,
    MenuItemSerializer,
    OrderFeedbackSerializer,
    ReservationCreateSerializer,
    ReservationSerializer,
    SalesRecordSerializer,
    SessionItemWriteSerializer,
    TableSerializer,
    TableSessionSerializer,
)
from .utils import calculate_bill


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

@extend_schema_view(
    list=extend_schema(summary='List menu items', tags=['menu']),
    retrieve=extend_schema(summary='Get a menu item', tags=['menu']),
    create=extend_schema(summary='Create a menu item', tags=['menu']),
    update=extend_schema(summary='Replace a menu item', tags=['menu']),
    partial_update=extend_schema(summary='Update a menu item', tags=['menu']),
    destroy=extend_schema(summary='Delete a menu item', tags=['menu']),
)
class MenuItemViewSet(ModelViewSet):
    """CRUD for menu items with filtering, search, and stock/trending toggles."""

    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filterset_class = MenuItemFilter
    search_fields = ['name', 'description', 'allergens']
    ordering_fields = ['price', 'name', 'sort_order']

    def get_queryset(self):
        """
        The ``category=trending`` shorthand is handled inside ``MenuItemFilter``;
        this override is intentionally minimal.
        """
        return super().get_queryset()

    @extend_schema(summary='Toggle in_stock flag', tags=['menu'])
    @action(detail=True, methods=['post'], url_path='toggle_stock')
    def toggle_stock(self, request, pk=None):
        """Toggle the ``in_stock`` flag for a single menu item."""
        item = self.get_object()
        item.in_stock = not item.in_stock
        item.save(update_fields=['in_stock', 'updated_at'])
        return Response(MenuItemSerializer(item).data)

    @extend_schema(summary='Toggle trending flag', tags=['menu'])
    @action(detail=True, methods=['post'], url_path='toggle_trending')
    def toggle_trending(self, request, pk=None):
        """Toggle the ``trending`` flag for a single menu item."""
        item = self.get_object()
        item.trending = not item.trending
        item.save(update_fields=['trending', 'updated_at'])
        return Response(MenuItemSerializer(item).data)


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

@extend_schema_view(
    list=extend_schema(summary='List all tables', tags=['tables']),
    retrieve=extend_schema(summary='Get a table', tags=['tables']),
    create=extend_schema(summary='Create a table', tags=['tables']),
    update=extend_schema(summary='Replace a table', tags=['tables']),
    partial_update=extend_schema(summary='Update a table', tags=['tables']),
    destroy=extend_schema(summary='Delete a table', tags=['tables']),
)
class TableViewSet(ModelViewSet):
    """CRUD for dining tables with active-session and QR-redirect helpers."""

    queryset = Table.objects.all()
    serializer_class = TableSerializer
    search_fields = ['location']
    ordering_fields = ['number', 'status']

    @extend_schema(summary='Get active session for a table', tags=['tables'])
    @action(detail=True, methods=['get'], url_path='session')
    def session(self, request, pk=None):
        """Return the currently active TableSession for this table, if any."""
        table = self.get_object()
        try:
            sess = TableSession.objects.prefetch_related(
                'session_items__menu_item'
            ).get(table_num=table.number)
        except TableSession.DoesNotExist:
            return Response(
                {'detail': 'No active session for this table.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(TableSessionSerializer(sess).data)

    @extend_schema(summary='QR redirect for customer ordering page', tags=['tables'])
    @action(detail=True, methods=['get'], url_path='qr_redirect')
    def qr_redirect(self, request, pk=None):
        """Return the customer ordering URL for the given table number."""
        table = self.get_object()
        from .utils import generate_qr_url
        base = request.build_absolute_uri('/').rstrip('/')
        return Response({'url': generate_qr_url(table.number, base_url=base)})


# ---------------------------------------------------------------------------
# Table Sessions
# ---------------------------------------------------------------------------

class TableSessionViewSet(ViewSet):
    """
    Manage dine-in table sessions.

    list   GET  /api/sessions/
    retrieve GET /api/sessions/{table_num}/
    create POST /api/sessions/{table_num}/
    close  POST /api/sessions/{table_num}/close/
    mark_bill_printed POST /api/sessions/{table_num}/mark_bill_printed/
    generate_bill GET /api/sessions/{table_num}/generate_bill/
    """

    @extend_schema(summary='List all active sessions', tags=['sessions'])
    def list(self, request):
        """Return all currently open table sessions."""
        sessions = TableSession.objects.prefetch_related('session_items__menu_item').all()
        # Manual pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        total = sessions.count()
        paginated = sessions[start:end]
        return Response({
            'count': total,
            'next': None if end >= total else f'?page={page + 1}',
            'previous': None if page <= 1 else f'?page={page - 1}',
            'results': TableSessionSerializer(paginated, many=True).data,
        })

    @extend_schema(summary='Get a table session', tags=['sessions'])
    def retrieve(self, request, pk=None):
        """Return the active session for table ``pk``."""
        try:
            session = TableSession.objects.prefetch_related(
                'session_items__menu_item'
            ).get(table_num=pk)
        except TableSession.DoesNotExist:
            return Response(
                {'detail': 'No active session for this table.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(TableSessionSerializer(session).data)

    @extend_schema(summary='Add items to / start a table session', tags=['sessions'])
    def create(self, request, pk=None):
        """
        Add items to (or create) a session for table ``pk``.

        Expected body::

            {
                "customer_name": "Alice",
                "special_instructions": "...",
                "items": [{"id": 1, "qty": 2}]
            }
        """
        items_data = request.data.get('items', [])
        item_serializer = SessionItemWriteSerializer(data=items_data, many=True)
        if not item_serializer.is_valid():
            return Response(item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        customer_name = request.data.get('customer_name', '')
        special_instructions = request.data.get('special_instructions', '')
        session_type = request.data.get('session_type', TableSession.SESSION_TYPE_DINE_IN)
        discount_code = request.data.get('discount_code', '')

        with transaction.atomic():
            session, created = TableSession.objects.get_or_create(
                table_num=pk,
                defaults={
                    'customer_name': customer_name,
                    'special_instructions': special_instructions,
                    'session_type': session_type,
                    'discount_code': discount_code,
                },
            )
            if not created:
                if customer_name:
                    session.customer_name = customer_name
                if special_instructions:
                    sep = ' | ' if session.special_instructions else ''
                    session.special_instructions += sep + special_instructions
                session.save()

            # Validate and apply discount code if provided
            if discount_code and not session.discount_amount:
                try:
                    discount_obj = Discount.objects.get(code=discount_code)
                    if not discount_obj.is_valid():
                        raise InvalidDiscount()
                except Discount.DoesNotExist:
                    raise InvalidDiscount()

            # Validate stock before adding items
            for entry in item_serializer.validated_data:
                try:
                    menu_item = MenuItem.objects.get(pk=entry['id'])
                except MenuItem.DoesNotExist:
                    return Response(
                        {'detail': f'Menu item {entry["id"]} not found.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not menu_item.in_stock:
                    raise MenuItemOutOfStock(
                        detail=f'"{menu_item.name}" is currently out of stock.'
                    )
                si, _ = SessionItem.objects.get_or_create(
                    session=session,
                    menu_item=menu_item,
                    defaults={'price': menu_item.price, 'qty': 0},
                )
                si.qty += entry['qty']
                si.price = menu_item.price
                si.notes = entry.get('notes', si.notes)
                si.save()

            # Create kitchen order ticket
            if items_data:
                ko = KitchenOrder.objects.create(
                    table_num=pk,
                    customer_name=session.customer_name,
                    special_instructions=special_instructions,
                )
                for entry in item_serializer.validated_data:
                    menu_item = MenuItem.objects.get(pk=entry['id'])
                    KitchenOrderItem.objects.create(
                        order=ko,
                        name=menu_item.name,
                        qty=entry['qty'],
                        price=menu_item.price,
                        notes=entry.get('notes', ''),
                    )

        session.refresh_from_db()
        return Response(
            TableSessionSerializer(session).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(summary='Close a table session', tags=['sessions'])
    @action(detail=False, methods=['post'], url_path='(?P<pk>[^/.]+)/close')
    def close(self, request, pk=None):
        """Close a table session and archive it as a SalesRecord."""
        try:
            session = TableSession.objects.prefetch_related(
                'session_items__menu_item'
            ).get(table_num=pk)
        except TableSession.DoesNotExist:
            return Response(
                {'detail': 'No active session for this table.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        settings = CafeSettings.get_settings()
        items_snapshot = [
            {
                'id': si.menu_item.id,
                'name': si.menu_item.name,
                'qty': si.qty,
                'price': si.price,
            }
            for si in session.session_items.all()
        ]
        payment_method = request.data.get('payment_method', SalesRecord.PAYMENT_CASH)
        bill = calculate_bill(
            items_snapshot, settings.tax_rate, session.discount_amount
        )

        SalesRecord.objects.create(
            table_num=session.table_num,
            customer_name=session.customer_name,
            special_instructions=session.special_instructions,
            items_json=items_snapshot,
            subtotal=bill['subtotal'],
            discount_amount=bill['discount'],
            total=bill['total'],
            payment_method=payment_method,
            start_time=session.start_time,
        )
        session.delete()
        return Response({'detail': f'Table {pk} session closed.', 'total': bill['total']})

    @extend_schema(summary='Mark bill as printed', tags=['sessions'])
    @action(detail=False, methods=['post'], url_path='(?P<pk>[^/.]+)/mark_bill_printed')
    def mark_bill_printed(self, request, pk=None):
        """Set the ``bill_printed`` flag on the active session for table ``pk``."""
        updated = TableSession.objects.filter(table_num=pk).update(bill_printed=True)
        if not updated:
            return Response(
                {'detail': 'No active session for this table.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'detail': f'Bill printed flag set for table {pk}.'})

    @extend_schema(summary='Get full bill breakdown', tags=['sessions'])
    @action(detail=False, methods=['get'], url_path='(?P<pk>[^/.]+)/generate_bill')
    def generate_bill(self, request, pk=None):
        """Return a detailed bill breakdown (subtotal, discount, tax, total) for a session."""
        try:
            session = TableSession.objects.prefetch_related(
                'session_items__menu_item'
            ).get(table_num=pk)
        except TableSession.DoesNotExist:
            return Response(
                {'detail': 'No active session for this table.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        settings = CafeSettings.get_settings()
        items = [
            {'price': si.price, 'qty': si.qty}
            for si in session.session_items.all()
        ]
        bill = calculate_bill(items, settings.tax_rate, session.discount_amount)
        bill['tax_rate'] = settings.tax_rate
        bill['discount_code'] = session.discount_code
        return Response(BillBreakdownSerializer(bill).data)


# ---------------------------------------------------------------------------
# Kitchen Orders
# ---------------------------------------------------------------------------

@extend_schema_view(
    list=extend_schema(summary='List kitchen orders', tags=['kitchen']),
    retrieve=extend_schema(summary='Get a kitchen order', tags=['kitchen']),
    partial_update=extend_schema(summary='Patch a kitchen order', tags=['kitchen']),
    destroy=extend_schema(summary='Delete a kitchen order', tags=['kitchen']),
)
class KitchenOrderViewSet(ModelViewSet):
    """Manage kitchen order tickets with filtering and bulk operations."""

    queryset = KitchenOrder.objects.prefetch_related('order_items').all()
    serializer_class = KitchenOrderSerializer
    filterset_class = KitchenOrderFilter

    def get_queryset(self):
        """Support legacy ``?status=`` param alongside the filter backend."""
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter and not self.request.query_params.get('status__exact'):
            qs = qs.filter(status=status_filter)
        return qs

    def create(self, request, *args, **kwargs):
        """Kitchen orders are created by the system; direct creation is not allowed."""
        return Response(
            {'detail': 'Kitchen orders are created automatically when items are ordered.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request, *args, **kwargs):
        """Full replacement of kitchen orders is not supported; use PATCH."""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @extend_schema(summary='Update order status', tags=['kitchen'])
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Update the status of a single kitchen order."""
        order = self.get_object()
        new_status = request.data.get('status')
        valid = [s[0] for s in KitchenOrder.STATUS_CHOICES]
        if new_status not in valid:
            return Response(
                {'detail': f'Invalid status. Choose from: {valid}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = new_status
        if new_status == KitchenOrder.STATUS_COMPLETED:
            order.completed_at = timezone.now()
        order.save()
        return Response(KitchenOrderSerializer(order).data)

    @extend_schema(summary='Bulk-update kitchen order statuses', tags=['kitchen'])
    @action(detail=False, methods=['post'], url_path='bulk_update')
    def bulk_update(self, request):
        """
        Update the status of multiple kitchen orders at once.

        Expected body::

            {
                "ids": [1, 2, 3],
                "status": "completed"
            }
        """
        ids = request.data.get('ids', [])
        new_status = request.data.get('status')
        valid = [s[0] for s in KitchenOrder.STATUS_CHOICES]
        if new_status not in valid:
            return Response(
                {'detail': f'Invalid status. Choose from: {valid}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not ids:
            return Response(
                {'detail': 'Provide a non-empty list of ids.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        update_kwargs = {'status': new_status}
        if new_status == KitchenOrder.STATUS_COMPLETED:
            update_kwargs['completed_at'] = timezone.now()
        updated = KitchenOrder.objects.filter(pk__in=ids).update(**update_kwargs)
        return Response({'updated': updated})


# ---------------------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------------------

@extend_schema_view(
    list=extend_schema(summary='List reservations', tags=['reservations']),
    retrieve=extend_schema(summary='Get a reservation', tags=['reservations']),
    create=extend_schema(summary='Create a reservation', tags=['reservations']),
    update=extend_schema(summary='Replace a reservation', tags=['reservations']),
    partial_update=extend_schema(summary='Update a reservation', tags=['reservations']),
    destroy=extend_schema(summary='Cancel/delete a reservation', tags=['reservations']),
)
class ReservationViewSet(ModelViewSet):
    """CRUD for table reservations with conflict detection and lifecycle actions."""

    queryset = Reservation.objects.select_related('table').all()
    filterset_class = ReservationFilter
    search_fields = ['customer_name', 'customer_phone']
    ordering_fields = ['reserved_date', 'reserved_time', 'status']

    def get_serializer_class(self):
        """Use write serializer for mutating operations."""
        if self.action in ('create', 'update', 'partial_update'):
            return ReservationCreateSerializer
        return ReservationSerializer

    @extend_schema(summary='Confirm a reservation', tags=['reservations'])
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """Move a reservation from ``pending`` to ``confirmed``."""
        reservation = self.get_object()
        reservation.status = Reservation.STATUS_CONFIRMED
        reservation.save(update_fields=['status', 'updated_at'])
        return Response(ReservationSerializer(reservation).data)

    @extend_schema(summary='Seat a reservation (mark as seated)', tags=['reservations'])
    @action(detail=True, methods=['post'], url_path='seat')
    def seat(self, request, pk=None):
        """Mark the reservation as ``seated`` and update the table status."""
        reservation = self.get_object()
        reservation.status = Reservation.STATUS_SEATED
        reservation.save(update_fields=['status', 'updated_at'])
        Table.objects.filter(number=reservation.table.number).update(
            status=Table.STATUS_OCCUPIED
        )
        return Response(ReservationSerializer(reservation).data)

    @extend_schema(summary='Cancel a reservation', tags=['reservations'])
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Move a reservation to ``cancelled`` status."""
        reservation = self.get_object()
        reservation.status = Reservation.STATUS_CANCELLED
        reservation.save(update_fields=['status', 'updated_at'])
        return Response(ReservationSerializer(reservation).data)


# ---------------------------------------------------------------------------
# Sales Records (read-only)
# ---------------------------------------------------------------------------

@extend_schema_view(
    list=extend_schema(summary='List sales records', tags=['sales']),
    retrieve=extend_schema(summary='Get a sales record', tags=['sales']),
)
class SalesRecordViewSet(ModelViewSet):
    """Read-only access to archived sales records with date-range filtering."""

    queryset = SalesRecord.objects.all()
    serializer_class = SalesRecordSerializer
    filterset_class = SalesRecordFilter
    http_method_names = ['get', 'head', 'options']
    ordering_fields = ['closed_at', 'total', 'table_num']


# ---------------------------------------------------------------------------
# Order Feedback
# ---------------------------------------------------------------------------

@extend_schema_view(
    list=extend_schema(summary='List feedback', tags=['feedback']),
    retrieve=extend_schema(summary='Get feedback', tags=['feedback']),
    create=extend_schema(summary='Submit feedback', tags=['feedback']),
)
class OrderFeedbackViewSet(ModelViewSet):
    """Create and read customer feedback linked to closed sales records."""

    queryset = OrderFeedback.objects.select_related('session_record').all()
    serializer_class = OrderFeedbackSerializer
    http_method_names = ['get', 'post', 'head', 'options']
    ordering_fields = ['created_at', 'overall_rating']


# ---------------------------------------------------------------------------
# Discounts
# ---------------------------------------------------------------------------

@extend_schema_view(
    list=extend_schema(summary='List discounts', tags=['discounts']),
    retrieve=extend_schema(summary='Get a discount', tags=['discounts']),
    create=extend_schema(summary='Create a discount', tags=['discounts']),
    update=extend_schema(summary='Replace a discount', tags=['discounts']),
    partial_update=extend_schema(summary='Update a discount', tags=['discounts']),
    destroy=extend_schema(summary='Delete a discount', tags=['discounts']),
)
class DiscountViewSet(ModelViewSet):
    """CRUD for promotional discount codes with a validate action."""

    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    search_fields = ['code', 'description']
    ordering_fields = ['valid_until', 'value']

    @extend_schema(
        summary='Validate a discount code and calculate savings',
        request=DiscountValidateSerializer,
        tags=['discounts'],
    )
    @action(detail=False, methods=['post'], url_path='validate')
    def validate_code(self, request):
        """
        Validate a discount code and return the calculated discount amount.

        Expected body::

            {"code": "SAVE20", "subtotal": 500}
        """
        serializer = DiscountValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        subtotal = serializer.validated_data['subtotal']

        try:
            discount = Discount.objects.get(code=code)
        except Discount.DoesNotExist:
            raise InvalidDiscount()

        if not discount.is_valid():
            raise InvalidDiscount()

        if subtotal < discount.min_order_amount:
            return Response(
                {
                    'valid': False,
                    'detail': (
                        f'Minimum order amount is ₹{discount.min_order_amount}.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = discount.calculate_discount(subtotal)
        return Response({
            'valid': True,
            'code': code,
            'discount_amount': amount,
            'discount_type': discount.discount_type,
            'value': str(discount.value),
            'description': discount.description,
        })


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class StatsViewSet(ViewSet):
    """Aggregate analytics endpoints for the cafe dashboard."""

    @extend_schema(summary="Today's overview stats", tags=['stats'])
    def list(self, request):
        """
        Return today's summary statistics.

        Response includes: revenue, orders, avg_order, active_tables, feedback_avg.
        """
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_sales = SalesRecord.objects.filter(closed_at__gte=today_start)
        revenue = today_sales.aggregate(total=Sum('total'))['total'] or 0
        orders = today_sales.count()
        avg_order = round(revenue / orders) if orders > 0 else 0
        active_tables = TableSession.objects.count()
        feedback_avg = OrderFeedback.objects.filter(
            created_at__gte=today_start
        ).aggregate(avg=Avg('overall_rating'))['avg']
        return Response({
            'revenue': revenue,
            'orders': orders,
            'avg_order': avg_order,
            'active_tables': active_tables,
            'feedback_avg': round(float(feedback_avg), 2) if feedback_avg else None,
        })

    @extend_schema(
        summary='Top 10 menu items by qty sold',
        parameters=[
            OpenApiParameter('date_from', description='Filter from date (YYYY-MM-DD)'),
            OpenApiParameter('date_to', description='Filter to date (YYYY-MM-DD)'),
        ],
        tags=['stats'],
    )
    @action(detail=False, methods=['get'], url_path='top_items')
    def top_items(self, request):
        """Return the top 10 best-selling menu items by quantity sold."""
        from django.db.models import IntegerField, Sum
        from django.db.models.functions import Cast

        sales_qs = SalesRecord.objects.all()
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            sales_qs = sales_qs.filter(closed_at__date__gte=date_from)
        if date_to:
            sales_qs = sales_qs.filter(closed_at__date__lte=date_to)

        # Aggregate from items_json (JSONField)
        from collections import defaultdict
        item_totals: dict[str, dict] = defaultdict(lambda: {'name': '', 'qty': 0, 'revenue': 0})
        for record in sales_qs.only('items_json'):
            for item in record.items_json:
                key = str(item.get('id', item.get('name', '')))
                item_totals[key]['name'] = item.get('name', key)
                item_totals[key]['qty'] += item.get('qty', 0)
                item_totals[key]['revenue'] += item.get('price', 0) * item.get('qty', 0)

        sorted_items = sorted(item_totals.values(), key=lambda x: x['qty'], reverse=True)[:10]
        return Response(sorted_items)

    @extend_schema(summary='Revenue by hour for today', tags=['stats'])
    @action(detail=False, methods=['get'], url_path='hourly')
    def hourly(self, request):
        """Return hourly revenue buckets for today (0–23)."""
        from django.db.models.functions import ExtractHour
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        rows = (
            SalesRecord.objects
            .filter(closed_at__gte=today_start)
            .annotate(hour=ExtractHour('closed_at'))
            .values('hour')
            .annotate(revenue=Sum('total'))
            .order_by('hour')
        )
        return Response(list(rows))

    @extend_schema(summary='Revenue breakdown by food category', tags=['stats'])
    @action(detail=False, methods=['get'], url_path='category_breakdown')
    def category_breakdown(self, request):
        """Return total revenue and quantity sold grouped by menu category."""
        from collections import defaultdict
        totals: dict[str, dict] = defaultdict(lambda: {'category': '', 'qty': 0, 'revenue': 0})
        for record in SalesRecord.objects.only('items_json'):
            for item in record.items_json:
                cat = item.get('category', 'unknown')
                totals[cat]['category'] = cat
                totals[cat]['qty'] += item.get('qty', 0)
                totals[cat]['revenue'] += item.get('price', 0) * item.get('qty', 0)
        return Response(sorted(totals.values(), key=lambda x: x['revenue'], reverse=True))


# ---------------------------------------------------------------------------
# Cafe Settings
# ---------------------------------------------------------------------------

class CafeSettingsViewSet(ViewSet):
    """Get or update the cafe-wide singleton configuration."""

    @extend_schema(summary='Get cafe settings', tags=['settings'])
    def list(self, request):
        """Return the current cafe settings."""
        settings = CafeSettings.get_settings()
        return Response(CafeSettingsSerializer(settings).data)

    @extend_schema(summary='Update cafe settings', tags=['settings'])
    def create(self, request):
        """Partially update the cafe settings (acts as PATCH on singleton)."""
        settings = CafeSettings.get_settings()
        serializer = CafeSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
