from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^feedback/', include('zenaida.contrib.feedback.urls')),
    url(r'^', include('brambling.urls')),
)
