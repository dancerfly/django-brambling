from rest_framework import serializers, viewsets
from rest_framework.permissions import BasePermission, SAFE_METHODS

from brambling.models import (
    DanceStyle,
    Organization,
)


class OrganizationPermission(BasePermission):
    def has_permission(self, request, view):
        # For now, disallow creation via the API.
        if request.method == 'POST':
            return False
        return True

    def has_object_permission(self, request, view, org):
        # Anyone can get a list or detail view.
        if request.method in SAFE_METHODS:
            return True

        # Anyone who can edit the org also has RUD permissions.
        if request.user.has_perm('edit', org):
            return True

        # Disallow deletion (for now, just a blanket).
        if request.method == 'DELETE':
            return False

        return False


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    """Serializes public data for an organization."""
    dance_styles = serializers.SlugRelatedField(
        slug_field='name',
        queryset=DanceStyle.objects.all(),
        many=True,
    )
    link = serializers.HyperlinkedIdentityField(view_name='organization-detail')

    class Meta:
        model = Organization
        fields = (
            'id', 'link', 'name', 'slug', 'description', 'website_url', 'facebook_url',
            'banner_image', 'city', 'state_or_province', 'country',
            'dance_styles',
        )


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [OrganizationPermission]
