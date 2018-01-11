from django.core.urlresolvers import reverse
from rest_framework import serializers, viewsets

from brambling.api.v1.permissions import BaseEventPermission
from brambling.models import ItemImage


class ItemImagePermission(BaseEventPermission):
    def has_object_permission(self, request, view, itemimage):
        return self._has_event_permission(request, itemimage.item.event)


class ItemImageSerializer(serializers.HyperlinkedModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='itemimage-detail')
    resize_endpoint = serializers.SerializerMethodField()

    class Meta:
        model = ItemImage
        fields = ('id', 'link', 'item', 'order', 'image', 'resize_endpoint')

    def get_resize_endpoint(self, obj):
        request = self.context.get('request', None)

        assert request is not None, (
            "`%s` requires the request in the serializer"
            " context. Add `context={'request': request}` when instantiating "
            "the serializer." % self.__class__.__name__
        )

        url = reverse('daguerre_ajax_adjustment_info', kwargs={'storage_path': obj.image.name})

        return request.build_absolute_uri(url)


class ItemImageViewSet(viewsets.ModelViewSet):
    queryset = ItemImage.objects.all()
    serializer_class = ItemImageSerializer
    permission_classes = [ItemImagePermission]
