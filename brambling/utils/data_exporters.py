import csv
import io

from django import forms

__all__ = ('BaseModelCSVExporter', 'AttendeeCSVExporter')


class BaseModelCSVExporter(object):
    """
    A class that is responsible for taking a queryset and returning
    it as a CSV formatted string with the render method.

    It takes two arguments:

    1. The queryset to be exported.
    2. The fields as a list of 2-tuples of the format
       ("Field Verbose Name", "field_name").
       `field_name` can be the name of an attribute on the model
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
            return fields
        # Default to all fields:
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
            raise AttributeError

        if callable(val):
            val = val()

        return val

    def get_form_class(self):
        return forms.Form

    @property
    def form(self):
        if not hasattr(self, '_form'):
            fields = {
                name[1]: forms.BooleanField(label=name[0], required=False)
                for name in self.FIELD_OPTIONS}
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

    #: A list of all possible fields
    FIELD_OPTIONS = (
        ("ID", "pk"),
        ("Name", "get_full_name"),
        ("Given Name", "given_name"),
        ("Surname", "surname"),
        ("Middle Name", "middle_name"),
        ("Pass Type", "pass_type"),
        ("Pass Status", "pass_status"),
    )

    # Methods to be used as fields
    def pass_type(self, obj):
        return "{}: {}".format(
            obj.event_pass.item_option.item.name,
            obj.event_pass.item_option.name)

    def pass_status(self, obj):
        return obj.event_pass.status
