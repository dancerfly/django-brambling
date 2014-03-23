from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.forms.models import modelform_factory
from django.http import Http404
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
    TemplateView)

from brambling.forms import EventForm, UserInfoForm, HouseForm
from brambling.models import Event, UserInfo, House


def home(request):
    if request.user.is_authenticated():
        return Dashboard.as_view()(request)
    else:
        return EventListView.as_view()(request)


class Dashboard(TemplateView):
    template_name = "brambling/dashboard.html"

    def get_context_data(self):
        current_user = self.request.user
        events = Event.objects.filter(privacy=Event.PUBLIC)
        query = Q(owner=current_user) | Q(editors=current_user)
        your_events = Event.objects.filter(query)
        return {'events': events, 'your_events': your_events}

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Dashboard, self).dispatch(*args, **kwargs)


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

    def get_queryset(self):
        queryset = super(EventDetailView, self).get_queryset()
        return queryset.prefetch_related('editors')


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

    def form_valid(self, form, *args, **kwargs):
        "Force form owner to be the current user."
        form.instance.owner = self.request.user
        return super(EventCreateView, self).form_valid(form, *args, **kwargs)

    def get_initial(self):
        "Instantiate form with owner as current user."
        return {'owner': self.request.user}

    def get_form_class(self):
        return modelform_factory(self.model, form=self.form_class,
                                 exclude=('owner', 'editors'),
                                 formfield_callback=formfield_callback)


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


class UserInfoView(UpdateView):
    model = UserInfo
    form_class = UserInfoForm

    def get_object(self):
        try:
            return self.request.user.userinfo
        except UserInfo.DoesNotExist:
            return UserInfo(user=self.request.user)


class HouseView(UpdateView):
    model = House
    form_class = HouseForm

    def get_object(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return (House.objects.filter(residents=self.request.user).first() or
                House())

    def get_initial(self):
        initial = super(HouseView, self).get_initial()
        if self.object.pk is None:
            initial['residents'] = [self.request.user]
        return initial
