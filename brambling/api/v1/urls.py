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
    BoughtItemViewSet,
    ItemViewSet,
    ItemImageViewSet,
    ItemOptionViewSet,
)


router = DefaultRouter()
router.register('housingcategory', HousingCategoryViewSet)
router.register('environmentalfactor', EnvironmentalFactorViewSet)
router.register('dancestyle', DanceStyleViewSet)
router.register('organization', OrganizationViewSet)
router.register('event', EventViewSet)
router.register('attendee', AttendeeViewSet)
router.register('eventhousing', EventHousingViewSet)
router.register('order', OrderViewSet)
router.register('boughtitem', BoughtItemViewSet)
router.register('item', ItemViewSet)
router.register('itemimage', ItemImageViewSet)
router.register('itemoption', ItemOptionViewSet)


urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
)
