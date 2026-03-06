from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CafeSettingsViewSet,
    KitchenOrderViewSet,
    MenuItemViewSet,
    SalesRecordViewSet,
    StatsViewSet,
    TableSessionViewSet,
)

router = DefaultRouter()
router.register(r'menu', MenuItemViewSet, basename='menu')
router.register(r'kitchen', KitchenOrderViewSet, basename='kitchen')
router.register(r'sales', SalesRecordViewSet, basename='sales')
router.register(r'stats', StatsViewSet, basename='stats')
router.register(r'settings', CafeSettingsViewSet, basename='settings')

# Sessions are keyed by table number, not a standard pk
sessions_urls = [
    path('', TableSessionViewSet.as_view({'get': 'list'}), name='session-list'),
    path('<int:pk>/', TableSessionViewSet.as_view({'get': 'retrieve', 'post': 'create'}), name='session-detail'),
    path('<int:pk>/close/', TableSessionViewSet.as_view({'post': 'close'}), name='session-close'),
    path('<int:pk>/mark_bill_printed/', TableSessionViewSet.as_view({'post': 'mark_bill_printed'}), name='session-bill'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('sessions/', include(sessions_urls)),
]
