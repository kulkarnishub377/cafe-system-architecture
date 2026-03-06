from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from .models import (
    CafeSettings,
    KitchenOrder,
    KitchenOrderItem,
    MenuItem,
    SalesRecord,
    SessionItem,
    TableSession,
)
from .serializers import (
    CafeSettingsSerializer,
    KitchenOrderSerializer,
    MenuItemSerializer,
    SalesRecordSerializer,
    SessionItemWriteSerializer,
    TableSessionSerializer,
)


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

class MenuItemViewSet(ModelViewSet):
    """CRUD for menu items plus a stock-toggle action."""

    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        if category and category != 'all':
            if category == 'trending':
                qs = qs.filter(trending=True)
            else:
                qs = qs.filter(category=category)
        return qs

    @action(detail=True, methods=['post'], url_path='toggle_stock')
    def toggle_stock(self, request, pk=None):
        """Toggle the in_stock flag for a single menu item."""
        item = self.get_object()
        item.in_stock = not item.in_stock
        item.save(update_fields=['in_stock'])
        return Response(MenuItemSerializer(item).data)


# ---------------------------------------------------------------------------
# Table Sessions
# ---------------------------------------------------------------------------

class TableSessionViewSet(ViewSet):
    """
    Manage dine-in table sessions.

    list   GET  /api/sessions/              → all active sessions
    retrieve GET /api/sessions/{table_num}/ → session detail
    create POST /api/sessions/{table_num}/  → add items / start session
    close  POST /api/sessions/{table_num}/close/
    mark_bill_printed POST /api/sessions/{table_num}/mark_bill_printed/
    """

    def list(self, request):
        sessions = TableSession.objects.prefetch_related('session_items__menu_item').all()
        serializer = TableSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            session = TableSession.objects.prefetch_related(
                'session_items__menu_item'
            ).get(table_num=pk)
        except TableSession.DoesNotExist:
            return Response({'detail': 'No active session for this table.'}, status=404)
        return Response(TableSessionSerializer(session).data)

    def create(self, request, pk=None):
        """
        Add items to (or create) a session for table `pk`.

        Expected body:
        {
            "customer_name": "Alice",           // optional
            "special_instructions": "...",      // optional
            "items": [{"id": 1, "qty": 2}, ...]
        }
        """
        items_data = request.data.get('items', [])
        item_serializer = SessionItemWriteSerializer(data=items_data, many=True)
        if not item_serializer.is_valid():
            return Response(item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        customer_name = request.data.get('customer_name', '')
        special_instructions = request.data.get('special_instructions', '')

        with transaction.atomic():
            session, created = TableSession.objects.get_or_create(
                table_num=pk,
                defaults={
                    'customer_name': customer_name,
                    'special_instructions': special_instructions,
                },
            )
            if not created:
                if customer_name:
                    session.customer_name = customer_name
                if special_instructions:
                    sep = ' | ' if session.special_instructions else ''
                    session.special_instructions += sep + special_instructions
                session.save()

            for entry in item_serializer.validated_data:
                try:
                    menu_item = MenuItem.objects.get(pk=entry['id'])
                except MenuItem.DoesNotExist:
                    return Response(
                        {'detail': f'Menu item {entry["id"]} not found.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                si, _ = SessionItem.objects.get_or_create(
                    session=session,
                    menu_item=menu_item,
                    defaults={'price': menu_item.price, 'qty': 0},
                )
                si.qty += entry['qty']
                si.price = menu_item.price
                si.save()

            # Also create kitchen order ticket
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
                    )

        session.refresh_from_db()
        return Response(
            TableSessionSerializer(session).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='(?P<pk>[^/.]+)/close')
    def close(self, request, pk=None):
        """Close a table session and archive it to SalesRecord."""
        try:
            session = TableSession.objects.prefetch_related(
                'session_items__menu_item'
            ).get(table_num=pk)
        except TableSession.DoesNotExist:
            return Response({'detail': 'No active session for this table.'}, status=404)

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
        subtotal = sum(i['price'] * i['qty'] for i in items_snapshot)
        total = round(subtotal * (1 + settings.tax_rate / 100))

        SalesRecord.objects.create(
            table_num=session.table_num,
            customer_name=session.customer_name,
            special_instructions=session.special_instructions,
            items_json=items_snapshot,
            subtotal=subtotal,
            total=total,
            start_time=session.start_time,
        )
        session.delete()
        return Response({'detail': f'Table {pk} session closed.', 'total': total})

    @action(detail=False, methods=['post'], url_path='(?P<pk>[^/.]+)/mark_bill_printed')
    def mark_bill_printed(self, request, pk=None):
        updated = TableSession.objects.filter(table_num=pk).update(bill_printed=True)
        if not updated:
            return Response({'detail': 'No active session for this table.'}, status=404)
        return Response({'detail': f'Bill printed flag set for table {pk}.'})


# ---------------------------------------------------------------------------
# Kitchen Orders
# ---------------------------------------------------------------------------

class KitchenOrderViewSet(ModelViewSet):
    """Manage kitchen order tickets."""

    queryset = KitchenOrder.objects.prefetch_related('order_items').all()
    serializer_class = KitchenOrderSerializer
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Update the status of a kitchen order."""
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


# ---------------------------------------------------------------------------
# Sales & Analytics
# ---------------------------------------------------------------------------

class SalesRecordViewSet(ModelViewSet):
    """Read-only access to archived sales records."""

    queryset = SalesRecord.objects.all()
    serializer_class = SalesRecordSerializer
    http_method_names = ['get', 'head', 'options']


class StatsViewSet(ViewSet):
    """Aggregate statistics endpoints."""

    def list(self, request):
        """Today's summary stats."""
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_sales = SalesRecord.objects.filter(closed_at__gte=today_start)
        revenue = today_sales.aggregate(total=Sum('total'))['total'] or 0
        orders = today_sales.count()
        avg_order = round(revenue / orders) if orders > 0 else 0
        active_tables = TableSession.objects.count()
        return Response({
            'revenue': revenue,
            'orders': orders,
            'active_tables': active_tables,
            'avg_order': avg_order,
        })


# ---------------------------------------------------------------------------
# Cafe Settings
# ---------------------------------------------------------------------------

class CafeSettingsViewSet(ViewSet):
    """Get or update cafe-wide configuration."""

    def list(self, request):
        settings = CafeSettings.get_settings()
        return Response(CafeSettingsSerializer(settings).data)

    def create(self, request):
        settings = CafeSettings.get_settings()
        serializer = CafeSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

