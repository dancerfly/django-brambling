from rest_framework import serializers, viewsets

from brambling.api.v1.permissions import BaseEventPermission
from brambling.models import (
    DanceStyle,
    Event,
)


class EventPermission(BaseEventPermission):
    def has_object_permission(self, request, view, event):
        # Disallow deletion of events (for now, just a blanket).
        if request.method == 'DELETE':
            return False

        return self._has_event_permission(request, event)


class EventSerializer(serializers.HyperlinkedModelSerializer):
    """Serializes public data for an event."""
    dance_styles = serializers.SlugRelatedField(
        slug_field='name',
        queryset=DanceStyle.objects.all(),
        many=True,
    )
    link = serializers.HyperlinkedIdentityField(view_name='event-detail')

    class Meta:
        model = Event
        fields = (
            'id', 'link', 'name', 'slug', 'description', 'website_url',
            'facebook_url', 'banner_image', 'city', 'state_or_province',
            'country', 'start_date', 'end_date', 'start_time', 'end_time',
            'dance_styles', 'has_dances', 'has_classes', 'liability_waiver',
            'organization', 'collect_housing_data', 'collect_survey_data',
            'timezone', 'currency', 'cart_timeout'
        )


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [EventPermission]
