from rest_framework import serializers, viewsets

from brambling.api.v1.permissions import IsAdminUserOrReadOnly
from brambling.models import DanceStyle


class DanceStyleSerializer(serializers.ModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='dancestyle-detail')

    class Meta:
        model = DanceStyle
        fields = ('link', 'name',)


class DanceStyleViewSet(viewsets.ModelViewSet):
    queryset = DanceStyle.objects.all()
    serializer_class = DanceStyleSerializer
    permission_classes = [IsAdminUserOrReadOnly]
