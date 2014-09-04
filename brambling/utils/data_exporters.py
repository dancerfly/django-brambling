import csv
import io

__all__ = ('BaseModelCSVExporter', 'AttendeeCSVExporter')


class BaseModelCSVExporter(object):
    def __init__(self, queryset):
        self.queryset = queryset

    def get_display_fields(self):
        """
        Returns a list of fields to display. Should return a
        tuple of 2-tuples.

        """
        return NotImplementedError

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

    def render(self):
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
    def get_display_fields(self):
        return (
            # ("Verbose Name", "method_or_attribute_name"),
            ("ID", "pk"),
            ("Name", "get_full_name"),
            ("Given Name", "given_name"),
            ("Surname", "surname"),
            ("Middle Name", "middle_name"),
        )
