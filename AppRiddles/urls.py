
from django.conf.urls import url,re_path
from . import views

app_name = 'AppRiddles'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^([0-9]+)/$', views.detail, name='detail'),
    url(r'^([0-9]+)/answer/$', views.answer, name='answer'),
    url(r'^register/$', views.RegisterFormView.as_view()),
    url(r'^login/$', views.LoginFormView.as_view()),
    url(r'^logout/$', views.LogoutView.as_view()),
    url(r'^password-change/$', views.PasswordChangeView.as_view()),
    url(r'^([0-9]+)/post/$', views.post, name='post'),
    url(r'^([0-9]+)/msg_list/$', views.msg_list, name='msg_list'),
    re_path(r'^admin/$', views.admin, name='admin'),
    re_path(r'^post_riddle/$', views.post_riddle, name='post_riddle'),
    re_path(r'^subscribe/$', views.SubscribeView.as_view()),
    re_path(r'^unsubscribe/$', views.unsubscribe, name='unsubscribe'),

]

