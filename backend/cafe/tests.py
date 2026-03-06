"""
Tests for # 91 VRS Cafe API.

Run with:
    python manage.py test cafe
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import (
    CafeSettings,
    KitchenOrder,
    MenuItem,
    SalesRecord,
    SessionItem,
    TableSession,
)


def make_item(**kwargs):
    """Helper: create a MenuItem with sensible defaults."""
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


class MenuItemTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.item = make_item(name='Espresso', price=120, category='coffee')

    def test_list_menu(self):
        resp = self.client.get('/api/menu/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_filter_by_category(self):
        make_item(name='Burger', price=300, category='burgers')
        resp = self.client.get('/api/menu/?category=coffee')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['name'], 'Espresso')

    def test_filter_trending(self):
        make_item(name='Trending Item', price=200, category='pizza', trending=True)
        resp = self.client.get('/api/menu/?category=trending')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['name'], 'Trending Item')

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


class TableSessionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.item1 = make_item(name='Cappuccino', price=180, category='coffee')
        self.item2 = make_item(name='Margherita', price=350, category='pizza')

    def test_create_session_with_items(self):
        resp = self.client.post(
            '/api/sessions/3/',
            {
                'customer_name': 'Alice',
                'items': [{'id': self.item1.pk, 'qty': 2}],
            },
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
        # Add more items to same session
        self.client.post(
            '/api/sessions/3/',
            {'items': [{'id': self.item1.pk, 'qty': 1}]},
            format='json',
        )
        si = SessionItem.objects.get(session__table_num=3, menu_item=self.item1)
        self.assertEqual(si.qty, 2)  # quantities should accumulate

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
        self.assertEqual(len(resp.data), 1)


class KitchenOrderTests(TestCase):
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
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['status'], 'pending')

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
        self.assertEqual(len(resp.data), 1)


class StatsTests(TestCase):
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


class CafeSettingsTests(TestCase):
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

