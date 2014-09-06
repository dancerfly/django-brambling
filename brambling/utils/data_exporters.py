import csv
import io
import itertools

from django import forms

__all__ = ('BaseModelCSVExporter', 'AttendeeCSVExporter')


def comma_separated_manager(attr_name):
    """
    Returns a function which takes a M2M manager on an object and
    returns it as a comma separated string.

    """

    def inner(self, obj):
        manager = getattr(obj, attr_name)
        return ", ".join([unicode(x) for x in manager.all()])
    return inner


class BaseModelCSVExporter(object):
    """
    A class that is responsible for taking a queryset and returning
    it as a CSV formatted string with the render method.

    It takes two arguments:

    1. The queryset to be exported.
    2. The fields as a list of 3-tuples of the format
       ("Field Verbose Name", "field_name", default), where default is True
       or False. `field_name` can be the name of an attribute on the model
       or an attribute on the Exporter subclass.

    """

    FIELD_OPTIONS = ()

    def __init__(self, queryset, data=None, fields=None, form_prefix=None):
        # Simple assignment:
        self.data = data or {}
        self.queryset = queryset
        self.fields = self.FIELD_OPTIONS
        self.form_prefix = form_prefix

        # More complex properties:
        self.is_bound = data is not None

    def get_display_fields(self):
        """
        Returns a tuple of 2-tuples in the form of
        ("Field Verbose Name", "field_name").

        """
        valid = self.is_bound and self.form.is_valid()
        if valid:
            cleaned_data = self.form.cleaned_data
            # Include fields which are marked True in the form:
            fields = [field
                      for field in self.fields
                      if cleaned_data[field[1]] == True]
            # Only return a list of fields if it isn't empty:
            if not fields == []:
                return fields
        # Otherwise default to all fields:
        return self.fields

    def get_queryset(self):
        return self.queryset

    def get_field_val(self, obj, key):
        """
        First look for values as attributes on the object, next check for a
        method on self (the exporter) and call it with the obj as the
        first argument.

        If the returned value is callable, call it and return that.
        """
        if hasattr(obj, key):
            val = getattr(obj, key)
        elif hasattr(self, key):
            meth = getattr(self, key)
            val = meth(obj)
        else:
            error_dict = {
                'attr': key,
                'model': obj.__class__.__name__,
                'exporter': self.__class__.__name__,
            }
            error_string = "{attr} does not exist as an attribute of {model} or {exporter}".format(**error_dict)
            raise AttributeError(error_string)

        if callable(val):
            val = val()

        return val

    def get_form_class(self):
        return forms.Form

    @property
    def form(self):
        """
        Returns a form of booleans for each field in FIELD_OPTIONS,
        bound with self.data if is not None.

        """

        if not hasattr(self, '_form'):
            fields = {}
            for field in self.FIELD_OPTIONS:
                boolean_field = forms.BooleanField(label=field[0], required=False, initial=field[2])
                fields.update({field[1]: boolean_field})

            Form = type(str('{}Form'.format(self.__class__.__name__)), (self.get_form_class(),), fields)

            if self.is_bound:
                self._form = Form(self.data, prefix=self.form_prefix)
            else:
                self._form = Form(prefix=self.form_prefix)

        return self._form

    def render(self):
        # TODO: rewrite this as a generator?

        object_list = self.get_queryset()
        csv_string = io.BytesIO()
        writer = csv.writer(csv_string)
        fields = self.get_display_fields()

        # Write Headers
        writer.writerow([x[0] for x in fields])

        for obj in object_list:
            row = []
            for field in fields:
                row.append(self.get_field_val(obj, field[1]))
            writer.writerow(row)

        return csv_string.getvalue()


class AttendeeCSVExporter(BaseModelCSVExporter):

    #: A list of ID related fields.
    IDENTIFICATION_FIELD_OPTIONS = (
        ("ID", "pk", True),
        ("Name", "get_full_name", True),
        ("Given Name", "given_name", True),
        ("Surname", "surname", True),
        ("Middle Name", "middle_name", True),
    )

    #: A list of contact related fields.
    CONTACT_FIELD_OPTIONS = (
        ("Email Address", "email", True),
        ("Phone Number", "phone", True),
    )

    #: A list of pass fields.
    PASS_FIELD_OPTIONS = (
        ("Pass Type", "pass_type", True),
        ("Pass Status", "pass_status", True),
    )

    #: A list of housing related fields.
    HOUSING_FIELD_OPTIONS = (
        ("Housing Status", "housing_status", True),
        ("Housing Nights", "housing_nights", True),
        ("Housing Environment Preference", "housing_preferences", True),
        ("Housing Environment Avoid", "environment_avoid", True),
        ("Attendee May Cause/Do", "environment_cause", True),
        ("Housing People Preference", "person_prefer", True),
        ("Housing People Avoid", "person_avoid", True),
        ("Other Housing Needs", "other_needs", True),
    )

    #: A list of order related fields.
    ORDER_FIELD_OPTIONS = (
        ("Order ID", "order_id", True),
        ("Order Placed By", "order_placed_by", True),
    )

    #: A list of miscellaneous fields.
    MISCELLANEOUS_FIELD_OPTIONS = (
        ("Liability Waiver Signed", "liability_waiver", True),
        ("Consent to be Photographed", "photo_consent", True),
    )

    FIELD_OPTIONS_BY_CATEGORY = (
        IDENTIFICATION_FIELD_OPTIONS,
        CONTACT_FIELD_OPTIONS,
        PASS_FIELD_OPTIONS,
        HOUSING_FIELD_OPTIONS,
        ORDER_FIELD_OPTIONS,
        MISCELLANEOUS_FIELD_OPTIONS,
    )

    #: A list of all possible display fields.
    FIELD_OPTIONS = reduce(tuple.__add__, FIELD_OPTIONS_BY_CATEGORY)

    # Methods to be used as fields
    def order_id(self, obj):
        return obj.order.pk

    def order_placed_by(self, obj):
        person = obj.order.person
        return "{} ({})".format(person.get_full_name(), person.email)

    def pass_type(self, obj):
        return "{}: {}".format(
            obj.event_pass.item_option.item.name,
            obj.event_pass.item_option.name)

    def pass_status(self, obj):
        return obj.event_pass.status

    housing_nights = comma_separated_manager("nights")
    housing_preferences = comma_separated_manager("housing_prefer")
    environment_avoid = comma_separated_manager("ef_avoid")
    environment_cause = comma_separated_manager("ef_cause")
