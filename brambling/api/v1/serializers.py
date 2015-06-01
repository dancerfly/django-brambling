from rest_framework import serializers

from brambling.models import (Order, EventHousing, BoughtItem,
                              EnvironmentalFactor, HousingCategory,
                              ItemOption, Item, ItemImage, Attendee, Event,
                              Organization, DanceStyle)


class HousingCategorySerializer(serializers.ModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='housingcategory-detail')

    class Meta:
        model = HousingCategory
        fields = ('link', 'name',)


class EnvironmentalFactorSerializer(serializers.ModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='environmentalfactor-detail')

    class Meta:
        model = EnvironmentalFactor
        fields = ('link', 'name',)


class DanceStyleSerializer(serializers.ModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='dancestyle-detail')

    class Meta:
        model = DanceStyle
        fields = ('link', 'name',)


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
            'timezone', 'currency',
        )


class AttendeeSerializer(serializers.HyperlinkedModelSerializer):
    ef_cause = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EnvironmentalFactor.objects.all(),
        many=True,
    )
    ef_avoid = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EnvironmentalFactor.objects.all(),
        many=True,
    )
    order = serializers.HyperlinkedRelatedField(view_name='order-detail', read_only=True)
    link = serializers.HyperlinkedIdentityField(view_name='attendee-detail')

    class Meta:
        model = Attendee
        fields = (
            'id', 'link', 'order', 'given_name', 'middle_name', 'surname',
            'name_order', 'basic_completed', 'email', 'phone',
            'liability_waiver', 'photo_consent', 'housing_status',
            'housing_completed', 'nights', 'ef_cause', 'ef_avoid',
            'person_prefer', 'person_avoid', 'housing_prefer',
            'housing_avoid', 'other_needs',
        )


class EventHousingSerializer(serializers.HyperlinkedModelSerializer):
    ef_present = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EnvironmentalFactor.objects.all(),
        many=True,
    )
    ef_avoid = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EnvironmentalFactor.objects.all(),
        many=True,
    )
    housing_categories = serializers.SlugRelatedField(
        slug_field='name',
        queryset=HousingCategory.objects.all(),
        many=True,
    )
    order = serializers.HyperlinkedRelatedField(view_name='order-detail', read_only=True)
    link = serializers.HyperlinkedIdentityField(view_name='eventhousing-detail')

    class Meta:
        model = EventHousing
        fields = (
            'id', 'link', 'event', 'order', 'contact_name', 'contact_email',
            'contact_phone', 'address', 'address_2', 'city',
            'state_or_province', 'zip_code', 'country',
            'public_transit_access', 'ef_present', 'ef_avoid', 'person_prefer',
            'person_avoid', 'housing_categories',
        )


class BoughtItemSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.ReadOnlyField()
    order = serializers.HyperlinkedRelatedField(view_name='order-detail', read_only=True)
    link = serializers.HyperlinkedIdentityField(view_name='boughtitem-detail')

    class Meta:
        model = BoughtItem
        fields = (
            'id', 'link', 'item_option', 'order', 'added', 'status', 'attendee'
        )


class OrderSerializer(serializers.HyperlinkedModelSerializer):
    bought_items = BoughtItemSerializer(many=True)
    eventhousing = EventHousingSerializer()
    person = serializers.StringRelatedField()
    link = serializers.HyperlinkedIdentityField(view_name='order-detail')

    class Meta:
        model = Order
        fields = (
            'id', 'link', 'event', 'person', 'email', 'code', 'cart_start_time',
            'bought_items', 'survey_completed', 'heard_through', 'heard_through_other',
            'send_flyers', 'send_flyers_address', 'send_flyers_address_2',
            'send_flyers_city', 'send_flyers_state_or_province',
            'send_flyers_zip', 'send_flyers_country', 'providing_housing',
            'notes', 'eventhousing',
        )

    def to_representation(self, obj):
        data = super(OrderSerializer, self).to_representation(obj)
        # Workaround for https://github.com/SmileyChris/django-countries/issues/106
        if data['send_flyers_country'] == '':
            data['send_flyers_country'] = ''
        return data


class ItemImageSerializer(serializers.HyperlinkedModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='itemimage-detail')

    class Meta:
        model = ItemImage
        fields = ('id', 'link', 'item', 'order', 'image')


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


class ItemSerializer(serializers.HyperlinkedModelSerializer):
    link = serializers.HyperlinkedIdentityField(view_name='item-detail')
    options = ItemOptionSerializer(many=True)
    images = ItemImageSerializer(many=True)

    class Meta:
        model = Item
        fields = ('id', 'link', 'name', 'description', 'event', 'created',
                  'last_modified', 'options', 'images')
