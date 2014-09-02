from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ageRecognition.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', 'apps.canvas.views.home', name='home'),

    url(r'^admin/', include(admin.site.urls)),

    # Facebook registration urls
    url(r'^facebook/', include('django_facebook.urls')),
    url(r'^accounts/', include('django_facebook.auth_urls')),

    # canvas urls
    (r'^', include('apps.canvas.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
