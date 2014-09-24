from django.conf.urls import patterns, include, url

urlpatterns = patterns('apps.canvas.views',
    url(r'^home/$', 'home', name='home'),
    url(r'^game/$', 'game', name='game'),
    url(r'^achievements/$', 'achievements', name='achievements'),
    url(r'^gallery/$', 'gallery', name='gallery'),
    url(r'^ranking/$', 'ranking', name='ranking'),
    url(r'^report/$', 'report', name='report'),
)