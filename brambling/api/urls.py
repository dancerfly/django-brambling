from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^v1/', include('brambling.api.v1.urls')),
)
