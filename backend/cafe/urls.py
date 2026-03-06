"""
URL routing for the cafe app.

All ViewSets are registered via DRF DefaultRouter.
Sessions (keyed by table_num) use manual URL patterns for backward compatibility.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuthViewSet,
    CafeSettingsViewSet,
    CustomerViewSet,
    DiscountViewSet,
    KitchenOrderViewSet,
    MenuItemViewSet,
    OrderFeedbackViewSet,
    ReservationViewSet,
    SalesRecordViewSet,
    StatsViewSet,
    TableSessionViewSet,
    TableViewSet,
)

router = DefaultRouter()
router.register(r'menu', MenuItemViewSet, basename='menu')
router.register(r'kitchen', KitchenOrderViewSet, basename='kitchen')
router.register(r'sales', SalesRecordViewSet, basename='sales')
router.register(r'stats', StatsViewSet, basename='stats')
router.register(r'settings', CafeSettingsViewSet, basename='settings')
router.register(r'tables', TableViewSet, basename='table')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'discounts', DiscountViewSet, basename='discount')
router.register(r'feedback', OrderFeedbackViewSet, basename='feedback')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'customer', CustomerViewSet, basename='customer')

# Sessions are keyed by table number, not a standard pk
sessions_urls = [
    path('', TableSessionViewSet.as_view({'get': 'list'}), name='session-list'),
    path(
        '<int:pk>/',
        TableSessionViewSet.as_view({'get': 'retrieve', 'post': 'create'}),
        name='session-detail',
    ),
    path(
        '<int:pk>/close/',
        TableSessionViewSet.as_view({'post': 'close'}),
        name='session-close',
    ),
    path(
        '<int:pk>/mark_bill_printed/',
        TableSessionViewSet.as_view({'post': 'mark_bill_printed'}),
        name='session-bill',
    ),
    path(
        '<int:pk>/generate_bill/',
        TableSessionViewSet.as_view({'get': 'generate_bill'}),
        name='session-generate-bill',
    ),
]

urlpatterns = [
    path('', include(router.urls)),
    path('sessions/', include(sessions_urls)),
]
