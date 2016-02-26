from django.conf.urls import patterns, url, include
from rest_framework.routers import DefaultRouter

from brambling.api.v1.views import (
    HousingCategoryViewSet,
    EnvironmentalFactorViewSet,
    DanceStyleViewSet,
    OrganizationViewSet,
    EventViewSet,
    AttendeeViewSet,
    EventHousingViewSet,
    OrderViewSet,
    OrderSearchViewSet,
    BoughtItemViewSet,
    ItemViewSet,
    ItemImageViewSet,
    ItemOptionViewSet,
    OrderDiscountViewSet,
)


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
router.register('orderdiscount', OrderDiscountViewSet)
router.register('organization', OrganizationViewSet)

urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
)
