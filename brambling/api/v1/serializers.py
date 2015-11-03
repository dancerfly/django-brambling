from django.core.urlresolvers import reverse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.fields import empty

from brambling.models import (Order, EventHousing, BoughtItem,
                              EnvironmentalFactor, HousingCategory,
                              ItemOption, Item, ItemImage, Attendee, Event,
                              Organization, DanceStyle, Discount, OrderDiscount,
                              BoughtItemDiscount)


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
            'timezone', 'currency', 'cart_timeout'
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
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Attendee
        fields = (
            'id', 'link', 'order', 'given_name', 'middle_name', 'surname',
            'name_order', 'basic_completed', 'email', 'phone',
            'liability_waiver', 'photo_consent', 'housing_status',
            'housing_completed', 'ef_cause', 'ef_avoid',
            'person_prefer', 'person_avoid', 'housing_prefer',
            'other_needs', 'full_name',
        )

    def get_full_name(self, obj):
        return obj.get_full_name()


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
    status = serializers.ChoiceField(choices=(BoughtItem.STATUS_CHOICES), default=BoughtItem.RESERVED)
    order = serializers.HyperlinkedRelatedField(view_name='order-detail', queryset=Order.objects.all())
    attendee = serializers.HyperlinkedRelatedField(view_name='attendee-detail', queryset=Attendee.objects.all(), allow_null=True)
    link = serializers.HyperlinkedIdentityField(view_name='boughtitem-detail')
    item_name = serializers.ReadOnlyField()
    item_description = serializers.ReadOnlyField()
    item_option_name = serializers.ReadOnlyField()
    price = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(BoughtItemSerializer, self).__init__(*args, **kwargs)

        if self.instance is not None:
            # If this is not a creation, set various fields to read-only
            self.fields['status'].read_only = True
            # Workaround for https://github.com/tomchristie/django-rest-framework/issues/3565
            self.fields['status'].default = empty
            self.fields['order'].read_only = True
            self.fields['item_option'].read_only = True

    def create(self, validated_data):
        item_option = validated_data['item_option']
        validated_data.update({
            'item_name': item_option.item.name,
            'item_description': item_option.item.description,
            'item_option_name': item_option.item.name,
            'price': item_option.price,
        })
        instance = super(BoughtItemSerializer, self).create(validated_data)

        discounts = OrderDiscount.objects.filter(
            order=validated_data['order'],
            discount__item_options=instance.item_option
        ).select_related('discount').distinct()
        if discounts:
            BoughtItemDiscount.objects.bulk_create([
                BoughtItemDiscount(discount=discount.discount,
                                   bought_item=instance,
                                   name=discount.discount.name,
                                   code=discount.discount.code,
                                   discount_type=discount.discount.discount_type,
                                   amount=discount.discount.amount)
                for discount in discounts
            ])

        if instance.order.cart_start_time is None:
            instance.order.cart_start_time = timezone.now()
            instance.order.save()

        return instance

    class Meta:
        model = BoughtItem
        fields = (
            'id', 'link', 'item_option', 'order', 'added', 'status', 'attendee',
            'item_name', 'item_description', 'item_option_name', 'price',
        )


class OrderDiscountSerializer(serializers.HyperlinkedModelSerializer):
    discount_name = serializers.CharField(read_only=True)
    discount_code = serializers.CharField()
    link = serializers.HyperlinkedIdentityField(view_name='orderdiscount-detail')
    order = serializers.HyperlinkedRelatedField(view_name='order-detail', queryset=Order.objects.all())

    def __init__(self, *args, **kwargs):
        super(OrderDiscountSerializer, self).__init__(*args, **kwargs)
        # If this is not a creation, set discount_code and order to read_only.
        if self.instance is not None:
            self.fields['discount_code'].read_only = True
            self.fields['order'].read_only = True

    def to_representation(self, instance):
        instance.discount_name = instance.discount.name
        instance.discount_code = instance.discount.code
        return super(OrderDiscountSerializer, self).to_representation(instance)

    def validate(self, data):
        if not data.get('discount_code'):
            raise serializers.ValidationError('Discount code is required.')
        try:
            self.discount = Discount.objects.get(code=data['discount_code'])
        except Discount.DoesNotExist:
            raise serializers.ValidationError("No discount with this code.")
        if data['order'].event != self.discount.event:
            raise serializers.ValidationError("Order and discount are for different events.")
        now = timezone.now()
        if self.discount.available_start > now or self.discount.available_end < now:
            raise serializers.ValidationError("Discount is not currently available.")
        if OrderDiscount.objects.filter(order=data['order'], discount=self.discount):
            raise serializers.ValidationError("Code has already been used.")
        return data

    def create(self, validated_data):
        validated_data.pop('discount_code')
        validated_data['discount'] = self.discount
        instance = super(OrderDiscountSerializer, self).create(validated_data)

        bought_items = BoughtItem.objects.filter(
            order=validated_data['order'],
            item_option__discount=self.discount,
        ).filter(status__in=(
            BoughtItem.UNPAID,
            BoughtItem.RESERVED,
        )).distinct()
        BoughtItemDiscount.objects.bulk_create([
            BoughtItemDiscount(discount=self.discount,
                               bought_item=bought_item,
                               name=self.discount.name,
                               code=self.discount.code,
                               discount_type=self.discount.discount_type,
                               amount=self.discount.amount)
            for bought_item in bought_items
        ])
        return instance

    def update(self, instance, validated_data):
        raise NotImplementedError("Order discounts can't be updated. They just exist.")

    class Meta:
        model = OrderDiscount
        fields = ('discount_name', 'discount_code', 'order', 'timestamp', 'link')


class OrderSerializer(serializers.HyperlinkedModelSerializer):
    bought_items = BoughtItemSerializer(many=True)
    discounts = OrderDiscountSerializer(many=True)
    eventhousing = EventHousingSerializer()
    person = serializers.StringRelatedField()
    link = serializers.HyperlinkedIdentityField(view_name='order-detail')
    event = serializers.HyperlinkedRelatedField(view_name='event-detail', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'link', 'event', 'person', 'email', 'code', 'cart_start_time',
            'bought_items', 'survey_completed', 'heard_through', 'heard_through_other',
            'send_flyers', 'send_flyers_address', 'send_flyers_address_2',
            'send_flyers_city', 'send_flyers_state_or_province',
            'send_flyers_zip', 'send_flyers_country', 'providing_housing',
            'notes', 'eventhousing', 'discounts',
        )

    def to_representation(self, obj):
        data = super(OrderSerializer, self).to_representation(obj)
        # Workaround for https://github.com/SmileyChris/django-countries/issues/106
        if data['send_flyers_country'] == '':
            data['send_flyers_country'] = ''
        return data


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
