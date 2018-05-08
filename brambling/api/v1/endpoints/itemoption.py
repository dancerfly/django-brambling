from rest_framework import serializers, viewsets

from brambling.api.v1.permissions import BaseEventPermission
from brambling.models import (
    BoughtItem,
    ItemOption,
)


class ItemOptionPermission(BaseEventPermission):
    def has_object_permission(self, request, view, itemoption):
        return self._has_event_permission(request, itemoption.item.event)


class ItemOptionSerializer(serializers.HyperlinkedModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='itemoption-detail')
    taken = serializers.SerializerMethodField()

    class Meta:
        model = ItemOption
        fields = ('id', 'link', 'item', 'name', 'price', 'total_number',
                  'available_start', 'available_end', 'remaining_display',
                  'order', 'taken')

    def get_taken(self, obj):
        if hasattr(obj, 'taken'):
            return obj.taken
        return obj.boughtitem_set.exclude(status=BoughtItem.REFUNDED).count()


class ItemOptionViewSet(viewsets.ModelViewSet):
    queryset = ItemOption.objects.all()
    serializer_class = ItemOptionSerializer
    permission_classes = [ItemOptionPermission]

    def get_queryset(self):
        qs = super(ItemOptionViewSet, self).get_queryset()
        qs = qs.extra(select={
            'taken': """
SELECT COUNT(*) FROM brambling_boughtitem WHERE
brambling_boughtitem.item_option_id = brambling_itemoption.id AND
brambling_boughtitem.status != 'refunded' AND
brambling_boughtitem.status != 'transferred'
"""
        })
        return qs
