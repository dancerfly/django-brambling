from rest_framework import serializers, viewsets

from brambling.api.v1.permissions import IsAdminUserOrReadOnly
from brambling.models import EnvironmentalFactor


class EnvironmentalFactorSerializer(serializers.ModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='environmentalfactor-detail')

    class Meta:
        model = EnvironmentalFactor
        fields = ('link', 'name',)


class EnvironmentalFactorViewSet(viewsets.ModelViewSet):
    queryset = EnvironmentalFactor.objects.all()
    serializer_class = EnvironmentalFactorSerializer
    permission_classes = [IsAdminUserOrReadOnly]
