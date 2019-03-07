from itertools import groupby

from django.db.models.query import QuerySet
from django.forms.models import ModelChoiceIterator

import floppyforms.__future__ as forms


class MemoModelForm(forms.ModelForm):
    # Subclass of ModelForm that memoizes querysets. For use in
    # complex formsets.
    def __init__(self, memo_dict, *args, **kwargs):
        self.memo_dict = memo_dict
        super(MemoModelForm, self).__init__(*args, **kwargs)

    def _model_and_qs(self, model_or_qs):
        if isinstance(model_or_qs, QuerySet):
            qs = model_or_qs
            model = qs.model
        else:
            model = model_or_qs
            qs = model.objects.all()

        return model, qs

    def get(self, model_or_qs, **kwargs):
        model, qs = self._model_and_qs(model_or_qs)
        key = frozenset(['get', model] + [item for item in kwargs.items()])
        if key not in self.memo_dict:
            try:
                self.memo_dict[key] = qs.get(**kwargs)
            except model.DoesNotExist:
                self.memo_dict[key] = None

        if self.memo_dict[key] is None:
            raise model.DoesNotExist
        return self.memo_dict[key]

    def filter(self, model_or_qs, **kwargs):
        model, qs = self._model_and_qs(model_or_qs)
        key = frozenset(['filter', model] + [item for item in kwargs.items()])
        if key not in self.memo_dict:
            self.memo_dict[key] = qs.filter(**kwargs)
        return self.memo_dict[key]

    def set_choices(self, field_name, model_or_qs, **kwargs):
        qs = self.filter(model_or_qs, **kwargs)
        field = self.fields[field_name]
        field.queryset = qs
        field.cache_choices = True
        field.choice_cache = [
            (field.prepare_value(obj), field.label_from_instance(obj))
            for obj in qs
        ]


class GroupedModelChoiceField(forms.ModelChoiceField):
    """
    A ModelChoiceField that groups choices by a specified field on
    the model.

    Heavily inspired by https://djangosnippets.org/snippets/2622/

    """

    def __init__(self, queryset, group_by_field, group_label=None, *args, **kwargs):
        """
        group_by_field is the name of a field on the model
        group_label is a function to return a label for each choice group

        Heavily inspired by https://djangosnippets.org/snippets/2622/
        """
        super(GroupedModelChoiceField, self).__init__(queryset, *args, **kwargs)
        self.group_by_field = group_by_field
        if group_label is None:
            self.group_label = lambda group: group
        else:
            self.group_label = group_label

    def _get_choices(self):
        """
        Exactly as per ModelChoiceField except returns new iterator class
        """
        if hasattr(self, '_choices'):
            return self._choices
        return GroupedModelChoiceIterator(self)
    choices = property(_get_choices, forms.ModelChoiceField._set_choices)


class GroupedModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    A ModelMultipleChoiceField that groups choices by a specified field on
    the model.

    Heavily inspired by https://djangosnippets.org/snippets/2622/

    """

    def __init__(self, queryset, group_by_field, group_label=None, *args, **kwargs):
        """
        group_by_field is the name of a field on the model
        group_label is a function to return a label for each choice group

        """
        super(GroupedModelMultipleChoiceField, self).__init__(queryset, *args, **kwargs)
        self.group_by_field = group_by_field
        if group_label is None:
            self.group_label = lambda group: group
        else:
            self.group_label = group_label

    def _get_choices(self):
        """
        Exactly as per ModelChoiceField except returns new iterator class
        """
        if hasattr(self, '_choices'):
            return self._choices
        return GroupedModelChoiceIterator(self)
    choices = property(_get_choices, forms.ModelChoiceField._set_choices)


class GroupedModelChoiceIterator(ModelChoiceIterator):
    """
    A ModelChoiceIterator that yields choices grouped by an attribute specified
    on the field's group_by property.

    Heavily inspired by https://djangosnippets.org/snippets/2622/

    """

    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        for group, choices in groupby(
            self.queryset.order_by(self.field.group_by_field),
            key=lambda row: getattr(row, self.field.group_by_field),
        ):
            yield (self.field.group_label(group), [self.choice(ch) for ch in choices])
