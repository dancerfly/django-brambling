from rest_framework import serializers, viewsets

from brambling.api.v1.permissions import IsAdminUserOrReadOnly
from brambling.models import HousingCategory


class HousingCategorySerializer(serializers.ModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='housingcategory-detail')

    class Meta:
        model = HousingCategory
        fields = ('link', 'name',)


class HousingCategoryViewSet(viewsets.ModelViewSet):
    queryset = HousingCategory.objects.all()
    serializer_class = HousingCategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]
