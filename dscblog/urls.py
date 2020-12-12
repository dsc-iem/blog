"""dscblog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import RedirectView
import dscblog.paths as paths


favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    path('', paths.index, name='index'),
    path('checkReferer', paths.check_referer),
    path('popular', paths.top25, name='popular'),
    path('new', paths.new_blogs),
    path('trending', paths.trending_blogs),
    path('topic/<str:topic>', paths.topic),
    path('login', RedirectView.as_view(url='/accounts/login', permanent=True)),
    path('None', RedirectView.as_view(
        url='/static/media/none.png', permanent=True)),
    path('explore', RedirectView.as_view(url='/', permanent=True)),
    path('cat/<str:topic>', paths.cat),
    path('<slug:slug>,<int:id>/', paths.blog, name='blog'),
    path('blog/<int:blog_id>/comments', paths.blog_comments),
    path('create', paths.create, name='create'),
    path('profile', paths.my_profile),
    path('@<str:username>/followers', paths.followers),
    path('userSettings', paths.user_settings),
    path('blog/<int:id>/settings', paths.blog_settings, name='blog_settings'),
    path('blog/<int:id>/edit', paths.blog_edit),
    path('blog/<int:id>/reactions', paths.blog_reactions),
    path('@<str:username>', paths.profile),
    path('accounts/', include('allauth.urls')),
    re_path(r'^favicon\.ico$', favicon_view),
    path('admin/', admin.site.urls),
    path('api/blog/title/set', paths.set_blog_title, name='set_blog_title'),
    path('api/blog/image/set', paths.set_blog_img),
    path('api/blog/content/set', paths.set_blog_content),
    path('api/blog/tag', paths.add_blog_topic),
    path('api/blog/untag', paths.remove_blog_topic),
    path('api/blog/publish', paths.publish_blog),
    path('api/blog/unpublish', paths.unpublish_blog),
    path('api/blog/delete', paths.delete_blog),
    path('api/user/follow', paths.follow_user),
    path('api/user/unfollow', paths.unfollow_user),
    path('api/blog/react', paths.blog_react),
    path('api/blog/unreact', paths.blog_unreact),
    path('api/blog/comment', paths.blog_comment),
    path('api/blog/uncomment', paths.blog_uncomment),
    path('api/blog/pingback', paths.pingback),
    path('api/alerts/new', paths.get_new_alerts),
    path('api/alerts/seen', paths.set_alerts_seen),
    path('info/privacy', paths.page_loader, {'page': 'info/privacy'}),
    path('info/terms', paths.page_loader, {'page': 'info/terms'}),
]

handler404 = 'dscblog.paths.page404'
