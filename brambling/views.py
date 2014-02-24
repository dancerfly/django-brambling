from django.forms.models import modelform_factory
from django.http import Http404
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from brambling.forms import EventForm
from brambling.models import Event


class EventListView(ListView):
    model = Event
    template_name = 'brambling/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        qs = super(EventListView, self).get_queryset()
        return qs.filter(privacy=Event.PUBLIC)


class EventDetailView(DetailView):
    model = Event
    template_name = 'brambling/event_detail.html'
    context_object_name = 'event'

    def get_object(self):
        obj = super(EventDetailView, self).get_object()
        if obj.privacy == Event.PRIVATE:
            user = self.request.user
            if not (user.is_authenticated() and user.is_active and
                    (user.is_superuser or user.pk == obj.owner_id or
                     obj.editors.filter(pk=user.pk).exists())):
                raise Http404
        return obj


class EventCreateView(CreateView):
    model = Event
    template_name = 'brambling/event_form.html'
    context_object_name = 'event'
    form_class = EventForm

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in self.http_method_names:
            if not request.user.is_authenticated():
                raise Http404
        return super(EventCreateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {'owner': self.request.user}

    def get_form_class(self):
        return modelform_factory(self.model, form=self.form_class,
                                 exclude=('owner', 'editors'))


class EventUpdateView(UpdateView):
    model = Event
    template_name = 'brambling/event_form.html'
    context_object_name = 'event'
    form_class = EventForm

    def get_object(self):
        obj = super(EventUpdateView, self).get_object()
        user = self.request.user
        if (user.is_authenticated() and user.is_active and
                (user.is_superuser or user.pk == obj.owner_id or
                 obj.editors.filter(pk=user.pk).exists())):
            return obj
        raise Http404
