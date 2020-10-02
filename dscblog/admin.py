from django.contrib import admin
from .models import User, Blog, Featured


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'name', 'email')
    readonly_fields = ('id',)


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'is_published')
    readonly_fields = ('id',)


@admin.register(Featured)
class FeaturedAdmin(admin.ModelAdmin):
    list_display = ('blog', 'priority')
