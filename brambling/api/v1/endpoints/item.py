from rest_framework import serializers, viewsets

from brambling.api.v1.permissions import BaseEventPermission
from brambling.api.v1.endpoints.itemoption import ItemOptionSerializer
from brambling.api.v1.endpoints.itemimage import ItemImageSerializer
from brambling.models import Item


class ItemPermission(BaseEventPermission):
    def has_object_permission(self, request, view, item):
        return self._has_event_permission(request, item.event)


class ItemSerializer(serializers.HyperlinkedModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='item-detail')
    options = ItemOptionSerializer(many=True)
    images = ItemImageSerializer(many=True)

    class Meta:
        model = Item
        fields = ('id', 'link', 'name', 'description', 'event', 'created',
                  'last_modified', 'options', 'images')


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [ItemPermission]

    def get_queryset(self):
        qs = Item.objects.all()

        if 'event' in self.request.GET:
            qs = qs.filter(event=self.request.GET['event'])

        return qs
