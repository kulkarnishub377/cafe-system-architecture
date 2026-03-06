"""
Comprehensive test suite for # 91 VRS Cafe API.

Run with:
    python manage.py test cafe

Covers all models, endpoints, filtering, discount logic,
reservation conflicts, bill generation, kitchen bulk updates,
and stats endpoints.
"""

from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import (
    CafeSettings,
    Discount,
    KitchenOrder,
    MenuItem,
    OrderFeedback,
    Reservation,
    SalesRecord,
    SessionItem,
    Table,
    TableSession,
)
from .utils import calculate_bill, get_greeting, generate_qr_url


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_item(**kwargs) -> MenuItem:
    """Create a MenuItem with sensible defaults."""
    defaults = {
        'name': 'Test Item',
        'price': 100,
        'category': 'coffee',
        'emoji': '☕',
        'is_veg': True,
        'in_stock': True,
        'trending': False,
        'description': 'A test item',
        'calories': 50,
    }
    defaults.update(kwargs)
    return MenuItem.objects.create(**defaults)


def make_table(number: int = 1, **kwargs) -> Table:
    """Create a Table with sensible defaults."""
    defaults = {'capacity': 4, 'location': 'Main Hall'}
    defaults.update(kwargs)
    return Table.objects.get_or_create(number=number, defaults=defaults)[0]


def make_discount(**kwargs) -> Discount:
    """Create a valid Discount with sensible defaults."""
    today = timezone.localdate()
    defaults = {
        'code': 'TEST10',
        'discount_type': Discount.DISCOUNT_TYPE_PERCENTAGE,
        'value': 10,
        'valid_from': today,
        'valid_until': today + timedelta(days=30),
    }
    defaults.update(kwargs)
    return Discount.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Utility function tests
# ---------------------------------------------------------------------------

class UtilsTests(TestCase):
    """Tests for utility helper functions."""

    def test_calculate_bill_no_discount(self):
        items = [{'price': 100, 'qty': 2}, {'price': 50, 'qty': 1}]
        result = calculate_bill(items, tax_rate=5.0)
        self.assertEqual(result['subtotal'], 250)
        self.assertEqual(result['discount'], 0)
        self.assertEqual(result['tax'], 12)  # round(250 * 0.05)
        self.assertEqual(result['total'], 262)

    def test_calculate_bill_with_discount(self):
        items = [{'price': 200, 'qty': 2}]  # 400 subtotal
        result = calculate_bill(items, tax_rate=5.0, discount_amount=50)
        self.assertEqual(result['subtotal'], 400)
        self.assertEqual(result['discount'], 50)
        self.assertEqual(result['tax'], 18)   # round(350 * 0.05)
        self.assertEqual(result['total'], 368)

    def test_calculate_bill_discount_exceeds_subtotal(self):
        items = [{'price': 100, 'qty': 1}]
        result = calculate_bill(items, tax_rate=5.0, discount_amount=200)
        self.assertEqual(result['subtotal'], 100)
        self.assertEqual(result['total'], 0)  # taxable = max(0, 100-200) = 0

    def test_get_greeting(self):
        self.assertEqual(get_greeting(6), 'Good Morning')
        self.assertEqual(get_greeting(13), 'Good Afternoon')
        self.assertEqual(get_greeting(18), 'Good Evening')
        self.assertEqual(get_greeting(23), 'Good Night')
        self.assertEqual(get_greeting(0), 'Good Night')

    def test_generate_qr_url(self):
        url = generate_qr_url(5, base_url='http://localhost:8000')
        self.assertEqual(url, 'http://localhost:8000/api/tables/5/qr_redirect/')


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class MenuItemModelTests(TestCase):
    """Unit tests for the MenuItem model."""

    def test_str_representation(self):
        item = make_item(name='Espresso', price=120)
        self.assertIn('Espresso', str(item))
        self.assertIn('120', str(item))

    def test_new_fields_exist(self):
        item = make_item(
            preparation_time_minutes=15,
            allergens='gluten',
            serving_size='250ml',
            sort_order=5,
        )
        self.assertEqual(item.preparation_time_minutes, 15)
        self.assertEqual(item.allergens, 'gluten')
        self.assertEqual(item.serving_size, '250ml')
        self.assertEqual(item.sort_order, 5)


class TableModelTests(TestCase):
    """Unit tests for the Table model."""

    def test_create_table(self):
        t = make_table(number=7, location='Terrace', capacity=6)
        self.assertEqual(t.number, 7)
        self.assertEqual(t.status, Table.STATUS_AVAILABLE)

    def test_str_representation(self):
        t = make_table(number=3)
        self.assertIn('3', str(t))


class DiscountModelTests(TestCase):
    """Unit tests for the Discount model."""

    def test_is_valid_active_discount(self):
        d = make_discount()
        self.assertTrue(d.is_valid())

    def test_is_invalid_expired_discount(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        d = make_discount(valid_until=yesterday)
        self.assertFalse(d.is_valid())

    def test_is_invalid_future_discount(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        d = make_discount(valid_from=tomorrow)
        self.assertFalse(d.is_valid())

    def test_is_invalid_inactive_discount(self):
        d = make_discount(is_active=False)
        self.assertFalse(d.is_valid())

    def test_is_invalid_exhausted_discount(self):
        d = make_discount(max_uses=5, used_count=5)
        self.assertFalse(d.is_valid())

    def test_calculate_percentage_discount(self):
        d = make_discount(discount_type=Discount.DISCOUNT_TYPE_PERCENTAGE, value=10)
        self.assertEqual(d.calculate_discount(500), 50)

    def test_calculate_fixed_discount(self):
        d = make_discount(discount_type=Discount.DISCOUNT_TYPE_FIXED, value=100)
        self.assertEqual(d.calculate_discount(500), 100)

    def test_fixed_discount_cannot_exceed_subtotal(self):
        d = make_discount(discount_type=Discount.DISCOUNT_TYPE_FIXED, value=1000)
        self.assertEqual(d.calculate_discount(200), 200)

    def test_discount_not_applied_below_min_order(self):
        d = make_discount(min_order_amount=300)
        self.assertEqual(d.calculate_discount(200), 0)


# ---------------------------------------------------------------------------
# Menu API tests
# ---------------------------------------------------------------------------

class MenuItemAPITests(TestCase):
    """API tests for /api/menu/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.item = make_item(name='Espresso', price=120, category='coffee')

    def test_list_menu(self):
        resp = self.client.get('/api/menu/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

    def test_filter_by_category(self):
        make_item(name='Burger', price=300, category='burgers')
        resp = self.client.get('/api/menu/?category=coffee')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 1)
        self.assertEqual(resp.data['results'][0]['name'], 'Espresso')

    def test_filter_trending(self):
        make_item(name='Trending Item', price=200, category='pizza', trending=True)
        resp = self.client.get('/api/menu/?category=trending')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 1)
        self.assertEqual(resp.data['results'][0]['name'], 'Trending Item')

    def test_filter_by_is_veg(self):
        make_item(name='Chicken Burger', price=300, category='burgers', is_veg=False)
        resp = self.client.get('/api/menu/?is_veg=true')
        self.assertEqual(resp.status_code, 200)
        for item in resp.data['results']:
            self.assertTrue(item['is_veg'])

    def test_filter_by_price_range(self):
        make_item(name='Cheap Item', price=50, category='snacks')
        make_item(name='Expensive Item', price=500, category='mains')
        resp = self.client.get('/api/menu/?price__gte=100&price__lte=200')
        self.assertEqual(resp.status_code, 200)
        for item in resp.data['results']:
            self.assertGreaterEqual(item['price'], 100)
            self.assertLessEqual(item['price'], 200)

    def test_create_menu_item(self):
        data = {
            'name': 'New Latte',
            'price': 180,
            'category': 'coffee',
            'emoji': '☕',
            'is_veg': True,
            'in_stock': True,
        }
        resp = self.client.post('/api/menu/', data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MenuItem.objects.count(), 2)

    def test_toggle_stock(self):
        self.assertTrue(self.item.in_stock)
        resp = self.client.post(f'/api/menu/{self.item.pk}/toggle_stock/')
        self.assertEqual(resp.status_code, 200)
        self.item.refresh_from_db()
        self.assertFalse(self.item.in_stock)
        # Toggle back
        resp = self.client.post(f'/api/menu/{self.item.pk}/toggle_stock/')
        self.assertEqual(resp.status_code, 200)
        self.item.refresh_from_db()
        self.assertTrue(self.item.in_stock)

    def test_toggle_trending(self):
        self.assertFalse(self.item.trending)
        resp = self.client.post(f'/api/menu/{self.item.pk}/toggle_trending/')
        self.assertEqual(resp.status_code, 200)
        self.item.refresh_from_db()
        self.assertTrue(self.item.trending)

    def test_update_menu_item(self):
        resp = self.client.patch(
            f'/api/menu/{self.item.pk}/',
            {'price': 150},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.price, 150)

    def test_delete_menu_item(self):
        resp = self.client.delete(f'/api/menu/{self.item.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MenuItem.objects.count(), 0)

    def test_is_available_field(self):
        resp = self.client.get(f'/api/menu/{self.item.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['is_available'])

    def test_search_by_name(self):
        make_item(name='Mocha Frappe', price=250, category='coffee')
        resp = self.client.get('/api/menu/?search=Frappe')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 1)


# ---------------------------------------------------------------------------
# Table API tests
# ---------------------------------------------------------------------------

class TableAPITests(TestCase):
    """API tests for /api/tables/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.table = make_table(number=1, location='Window')

    def test_list_tables(self):
        resp = self.client.get('/api/tables/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)

    def test_create_table(self):
        resp = self.client.post(
            '/api/tables/',
            {'number': 2, 'capacity': 4, 'location': 'Terrace'},
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Table.objects.count(), 2)

    def test_get_table_session_when_no_session(self):
        resp = self.client.get(f'/api/tables/{self.table.pk}/session/')
        self.assertEqual(resp.status_code, 404)

    def test_get_table_session_when_session_exists(self):
        item = make_item()
        self.client.post(
            f'/api/sessions/{self.table.number}/',
            {'items': [{'id': item.pk, 'qty': 1}]},
            format='json',
        )
        resp = self.client.get(f'/api/tables/{self.table.pk}/session/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['table_num'], self.table.number)

    def test_qr_redirect(self):
        resp = self.client.get(f'/api/tables/{self.table.pk}/qr_redirect/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('url', resp.data)
        self.assertIn(str(self.table.number), resp.data['url'])


# ---------------------------------------------------------------------------
# Reservation API tests
# ---------------------------------------------------------------------------

class ReservationAPITests(TestCase):
    """API tests for /api/reservations/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.table = make_table(number=5)
        self.tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
        self.res_time = '19:00:00'

    def _create_reservation(self, **kwargs):
        data = {
            'table': self.table.pk,
            'customer_name': 'Bob',
            'customer_phone': '9876543210',
            'party_size': 2,
            'reserved_date': self.tomorrow,
            'reserved_time': self.res_time,
        }
        data.update(kwargs)
        return self.client.post('/api/reservations/', data, format='json')

    def test_create_reservation(self):
        resp = self._create_reservation()
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_reservation_conflict(self):
        self._create_reservation()
        resp = self._create_reservation(customer_name='Charlie')
        self.assertEqual(resp.status_code, 409)

    def test_different_time_no_conflict(self):
        self._create_reservation()
        resp = self._create_reservation(reserved_time='20:00:00')
        self.assertEqual(resp.status_code, 201)

    def test_confirm_action(self):
        self._create_reservation()
        res = Reservation.objects.first()
        self.assertEqual(res.status, Reservation.STATUS_PENDING)
        resp = self.client.post(f'/api/reservations/{res.pk}/confirm/')
        self.assertEqual(resp.status_code, 200)
        res.refresh_from_db()
        self.assertEqual(res.status, Reservation.STATUS_CONFIRMED)

    def test_cancel_action(self):
        self._create_reservation()
        res = Reservation.objects.first()
        resp = self.client.post(f'/api/reservations/{res.pk}/cancel/')
        self.assertEqual(resp.status_code, 200)
        res.refresh_from_db()
        self.assertEqual(res.status, Reservation.STATUS_CANCELLED)

    def test_seat_action_updates_table(self):
        self._create_reservation()
        res = Reservation.objects.first()
        resp = self.client.post(f'/api/reservations/{res.pk}/seat/')
        self.assertEqual(resp.status_code, 200)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, Table.STATUS_OCCUPIED)

    def test_filter_by_status(self):
        self._create_reservation()
        res = Reservation.objects.first()
        resp_pending = self.client.get('/api/reservations/?status=pending')
        self.assertEqual(resp_pending.data['count'], 1)
        res.status = Reservation.STATUS_CONFIRMED
        res.save()
        resp_pending_after = self.client.get('/api/reservations/?status=pending')
        self.assertEqual(resp_pending_after.data['count'], 0)


# ---------------------------------------------------------------------------
# Table Session tests
# ---------------------------------------------------------------------------

class TableSessionTests(TestCase):
    """API tests for /api/sessions/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.item1 = make_item(name='Cappuccino', price=180, category='coffee')
        self.item2 = make_item(name='Margherita', price=350, category='pizza')

    def test_create_session_with_items(self):
        resp = self.client.post(
            '/api/sessions/3/',
            {'customer_name': 'Alice', 'items': [{'id': self.item1.pk, 'qty': 2}]},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TableSession.objects.count(), 1)
        session = TableSession.objects.first()
        self.assertEqual(session.table_num, 3)
        self.assertEqual(session.customer_name, 'Alice')
        self.assertEqual(SessionItem.objects.count(), 1)

    def test_add_items_to_existing_session(self):
        self.client.post(
            '/api/sessions/3/',
            {'items': [{'id': self.item1.pk, 'qty': 1}]},
            format='json',
        )
        self.client.post(
            '/api/sessions/3/',
            {'items': [{'id': self.item1.pk, 'qty': 1}]},
            format='json',
        )
        si = SessionItem.objects.get(session__table_num=3, menu_item=self.item1)
        self.assertEqual(si.qty, 2)

    def test_kitchen_order_created_on_session_post(self):
        self.client.post(
            '/api/sessions/3/',
            {'items': [{'id': self.item1.pk, 'qty': 1}]},
            format='json',
        )
        self.assertEqual(KitchenOrder.objects.count(), 1)

    def test_retrieve_session(self):
        self.client.post(
            '/api/sessions/3/',
            {'items': [{'id': self.item1.pk, 'qty': 1}]},
            format='json',
        )
        resp = self.client.get('/api/sessions/3/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['table_num'], 3)
        self.assertEqual(len(resp.data['items']), 1)

    def test_retrieve_nonexistent_session(self):
        resp = self.client.get('/api/sessions/99/')
        self.assertEqual(resp.status_code, 404)

    def test_session_total_includes_tax(self):
        CafeSettings.objects.update_or_create(pk=1, defaults={'tax_rate': 5.0})
        self.client.post(
            '/api/sessions/3/',
            {'items': [{'id': self.item1.pk, 'qty': 2}]},  # 2 × 180 = 360
            format='json',
        )
        resp = self.client.get('/api/sessions/3/')
        # 360 * 1.05 = 378
        self.assertEqual(resp.data['total'], 378)

    def test_close_session_creates_sales_record(self):
        self.client.post(
            '/api/sessions/3/',
            {'items': [{'id': self.item1.pk, 'qty': 1}]},
            format='json',
        )
        resp = self.client.post('/api/sessions/3/close/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(TableSession.objects.count(), 0)
        self.assertEqual(SalesRecord.objects.count(), 1)

    def test_close_nonexistent_session(self):
        resp = self.client.post('/api/sessions/99/close/')
        self.assertEqual(resp.status_code, 404)

    def test_mark_bill_printed(self):
        self.client.post(
            '/api/sessions/3/',
            {'items': [{'id': self.item1.pk, 'qty': 1}]},
            format='json',
        )
        resp = self.client.post('/api/sessions/3/mark_bill_printed/')
        self.assertEqual(resp.status_code, 200)
        session = TableSession.objects.get(table_num=3)
        self.assertTrue(session.bill_printed)

    def test_invalid_item_id_returns_400(self):
        resp = self.client.post(
            '/api/sessions/3/',
            {'items': [{'id': 9999, 'qty': 1}]},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_list_sessions(self):
        self.client.post(
            '/api/sessions/3/',
            {'items': [{'id': self.item1.pk, 'qty': 1}]},
            format='json',
        )
        resp = self.client.get('/api/sessions/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 1)

    def test_generate_bill_endpoint(self):
        CafeSettings.objects.update_or_create(pk=1, defaults={'tax_rate': 5.0})
        self.client.post(
            '/api/sessions/4/',
            {'items': [{'id': self.item1.pk, 'qty': 2}]},  # 2×180=360
            format='json',
        )
        resp = self.client.get('/api/sessions/4/generate_bill/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['subtotal'], 360)
        self.assertEqual(resp.data['discount'], 0)
        self.assertEqual(resp.data['total'], 378)

    def test_out_of_stock_item_rejected(self):
        self.item1.in_stock = False
        self.item1.save()
        resp = self.client.post(
            '/api/sessions/5/',
            {'items': [{'id': self.item1.pk, 'qty': 1}]},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)


# ---------------------------------------------------------------------------
# Kitchen Order tests
# ---------------------------------------------------------------------------

class KitchenOrderTests(TestCase):
    """API tests for /api/kitchen/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.item = make_item(name='Latte', price=180, category='coffee')

    def _place_order(self, table=1):
        self.client.post(
            f'/api/sessions/{table}/',
            {'items': [{'id': self.item.pk, 'qty': 1}]},
            format='json',
        )

    def test_kitchen_order_list(self):
        self._place_order()
        resp = self.client.get('/api/kitchen/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 1)
        self.assertEqual(resp.data['results'][0]['status'], 'pending')

    def test_update_status_to_preparing(self):
        self._place_order()
        order = KitchenOrder.objects.first()
        resp = self.client.patch(
            f'/api/kitchen/{order.pk}/status/',
            {'status': 'preparing'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'preparing')

    def test_update_status_to_completed_sets_timestamp(self):
        self._place_order()
        order = KitchenOrder.objects.first()
        self.client.patch(
            f'/api/kitchen/{order.pk}/status/',
            {'status': 'completed'},
            format='json',
        )
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')
        self.assertIsNotNone(order.completed_at)

    def test_invalid_status_returns_400(self):
        self._place_order()
        order = KitchenOrder.objects.first()
        resp = self.client.patch(
            f'/api/kitchen/{order.pk}/status/',
            {'status': 'invalid_status'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_filter_by_status(self):
        self._place_order(table=1)
        self._place_order(table=2)
        order = KitchenOrder.objects.first()
        self.client.patch(
            f'/api/kitchen/{order.pk}/status/',
            {'status': 'preparing'},
            format='json',
        )
        resp = self.client.get('/api/kitchen/?status=pending')
        self.assertEqual(len(resp.data['results']), 1)

    def test_bulk_update(self):
        self._place_order(table=1)
        self._place_order(table=2)
        ids = list(KitchenOrder.objects.values_list('pk', flat=True))
        resp = self.client.post(
            '/api/kitchen/bulk_update/',
            {'ids': ids, 'status': 'completed'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['updated'], 2)
        self.assertEqual(
            KitchenOrder.objects.filter(status='completed').count(), 2
        )

    def test_bulk_update_invalid_status(self):
        self._place_order()
        ids = list(KitchenOrder.objects.values_list('pk', flat=True))
        resp = self.client.post(
            '/api/kitchen/bulk_update/',
            {'ids': ids, 'status': 'bad'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_bulk_update_empty_ids(self):
        self._place_order()
        resp = self.client.post(
            '/api/kitchen/bulk_update/',
            {'ids': [], 'status': 'completed'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)


# ---------------------------------------------------------------------------
# Discount API tests
# ---------------------------------------------------------------------------

class DiscountAPITests(TestCase):
    """API tests for /api/discounts/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.discount = make_discount(code='SAVE20', discount_type=Discount.DISCOUNT_TYPE_PERCENTAGE, value=20)

    def test_list_discounts(self):
        resp = self.client.get('/api/discounts/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)

    def test_validate_valid_code(self):
        resp = self.client.post(
            '/api/discounts/validate/',
            {'code': 'SAVE20', 'subtotal': 500},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['valid'])
        self.assertEqual(resp.data['discount_amount'], 100)  # 20% of 500

    def test_validate_invalid_code(self):
        resp = self.client.post(
            '/api/discounts/validate/',
            {'code': 'BADCODE', 'subtotal': 500},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_validate_expired_code(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        make_discount(code='EXPIRED', valid_until=yesterday)
        resp = self.client.post(
            '/api/discounts/validate/',
            {'code': 'EXPIRED', 'subtotal': 500},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_validate_below_minimum_order(self):
        make_discount(code='MINORDER', min_order_amount=500)
        resp = self.client.post(
            '/api/discounts/validate/',
            {'code': 'MINORDER', 'subtotal': 100},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)


# ---------------------------------------------------------------------------
# Stats tests
# ---------------------------------------------------------------------------

class StatsTests(TestCase):
    """API tests for /api/stats/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.item = make_item(name='Mocha', price=200, category='coffee')

    def test_stats_empty(self):
        resp = self.client.get('/api/stats/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['revenue'], 0)
        self.assertEqual(resp.data['orders'], 0)
        self.assertEqual(resp.data['active_tables'], 0)

    def test_stats_reflect_closed_sessions(self):
        CafeSettings.objects.update_or_create(pk=1, defaults={'tax_rate': 5.0})
        self.client.post(
            '/api/sessions/1/',
            {'items': [{'id': self.item.pk, 'qty': 1}]},
            format='json',
        )
        self.client.post('/api/sessions/1/close/')
        resp = self.client.get('/api/stats/')
        self.assertEqual(resp.data['orders'], 1)
        self.assertEqual(resp.data['revenue'], 210)  # 200 × 1.05

    def test_top_items_endpoint(self):
        resp = self.client.get('/api/stats/top_items/')
        self.assertEqual(resp.status_code, 200)

    def test_hourly_endpoint(self):
        resp = self.client.get('/api/stats/hourly/')
        self.assertEqual(resp.status_code, 200)

    def test_category_breakdown_endpoint(self):
        resp = self.client.get('/api/stats/category_breakdown/')
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# Order Feedback tests
# ---------------------------------------------------------------------------

class OrderFeedbackTests(TestCase):
    """API tests for /api/feedback/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.sale = SalesRecord.objects.create(
            table_num=3,
            subtotal=300,
            total=315,
            start_time=timezone.now(),
        )

    def test_submit_feedback(self):
        resp = self.client.post(
            '/api/feedback/',
            {
                'session_record': self.sale.pk,
                'table_num': 3,
                'overall_rating': 5,
                'food_rating': 4,
                'service_rating': 5,
                'comment': 'Excellent!',
                'would_recommend': True,
            },
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(OrderFeedback.objects.count(), 1)

    def test_invalid_rating_rejected(self):
        resp = self.client.post(
            '/api/feedback/',
            {
                'session_record': self.sale.pk,
                'table_num': 3,
                'overall_rating': 6,  # invalid
            },
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_list_feedback(self):
        OrderFeedback.objects.create(
            session_record=self.sale,
            table_num=3,
            overall_rating=4,
        )
        resp = self.client.get('/api/feedback/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)


# ---------------------------------------------------------------------------
# Cafe Settings tests
# ---------------------------------------------------------------------------

class CafeSettingsTests(TestCase):
    """API tests for /api/settings/ endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_get_default_settings(self):
        resp = self.client.get('/api/settings/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('cafe_name', resp.data)

    def test_update_settings(self):
        resp = self.client.post(
            '/api/settings/',
            {'cafe_name': 'New Cafe Name', 'tax_rate': 10},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        settings = CafeSettings.get_settings()
        self.assertEqual(settings.cafe_name, 'New Cafe Name')
        self.assertEqual(settings.tax_rate, 10)

    def test_new_settings_fields_returned(self):
        resp = self.client.get('/api/settings/')
        self.assertIn('opening_time', resp.data)
        self.assertIn('closing_time', resp.data)
        self.assertIn('currency_symbol', resp.data)
        self.assertIn('footer_message', resp.data)
