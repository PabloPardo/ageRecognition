from django.conf.urls import patterns, include, url

urlpatterns = patterns('apps.canvas.views',
    url(r'^home/$', 'home', name='home'),
)