from django.conf.urls import patterns, include, url

urlpatterns = patterns('apps.canvas.views',
    url(r'^$', 'home', name='home'),
    url(r'^home/$', 'home', name='home'),
    url(r'^game/$', 'game', name='game'),
    url(r'^achievements/$', 'achievements', name='achievements'),
    url(r'^gallery/$', 'gallery', name='gallery'),
    url(r'^gallery/(?P<id_rm>\d+)/$', 'rm_image', name='rm_image'),
    url(r'^ranking/$', 'ranking', name='ranking'),
    url(r'^report/$', 'game', name='report'),
    url(r'^terms/$', 'terms', name='terms'),
    url(r'^privacy/$', 'privacy', name='privacy'),
    url(r'^help/$', 'help', name='help'),
    url(r'^prizes/$', 'prizes', name='prizes'),
    url(r'^test/$', 'test', name='test'),
)
