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
    path('login', RedirectView.as_view(url='/accounts/login', permanent=True)),
    path('<slug:slug>,<int:id>/', paths.blog, name='blog'),
    path('create', paths.create, name='create'),
    path('blog/<int:id>/settings', paths.blog_settings, name='blog_settings'),
    path('accounts/', include('allauth.urls')),
    re_path(r'^favicon\.ico$', favicon_view),
    path('admin/', admin.site.urls),
    path('api/blog/title/set', paths.set_blog_title, name='set_blog_title'),
    path('api/blog/image/set', paths.set_blog_img),
    path('api/blog/publish', paths.publish_blog),
    path('api/blog/unpublish', paths.unpublish_blog),
    path('api/blog/delete', paths.delete_blog),
]

handler404 = 'dscblog.paths.page404'
