from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from brambling.api.v1.endpoints.attendee import AttendeeViewSet
from brambling.api.v1.endpoints.boughtitem import BoughtItemViewSet
from brambling.api.v1.endpoints.dancestyle import DanceStyleViewSet
from brambling.api.v1.endpoints.environmentalfactor import EnvironmentalFactorViewSet
from brambling.api.v1.endpoints.event import EventViewSet
from brambling.api.v1.endpoints.eventhousing import EventHousingViewSet
from brambling.api.v1.endpoints.housingcategory import HousingCategoryViewSet
from brambling.api.v1.endpoints.item import ItemViewSet
from brambling.api.v1.endpoints.itemimage import ItemImageViewSet
from brambling.api.v1.endpoints.itemoption import ItemOptionViewSet
from brambling.api.v1.endpoints.order import OrderViewSet
from brambling.api.v1.endpoints.ordersearch import OrderSearchViewSet
from brambling.api.v1.endpoints.organization import OrganizationViewSet


router = DefaultRouter()
router.register('attendee', AttendeeViewSet)
router.register('boughtitem', BoughtItemViewSet)
router.register('dancestyle', DanceStyleViewSet)
router.register('environmentalfactor', EnvironmentalFactorViewSet)
router.register('event', EventViewSet)
router.register('eventhousing', EventHousingViewSet)
router.register('housingcategory', HousingCategoryViewSet)
router.register('item', ItemViewSet)
router.register('itemimage', ItemImageViewSet)
router.register('itemoption', ItemOptionViewSet)
router.register('order', OrderViewSet)
router.register('ordersearch', OrderSearchViewSet, base_name='ordersearch')
router.register('organization', OrganizationViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
