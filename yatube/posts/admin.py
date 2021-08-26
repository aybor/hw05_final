from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    search_fields = ('text',)
    list_filter = ('pub_date',)
    list_editable = ('group',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'description',
        'slug'
    )
    search_fields = 'description',
    empty_value_key = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'post',
        'author',
        'text',
        'created',
    )
    search_fields = ('text',)
    list_filter = ('post', 'author', 'created')
    list_editable = ('text',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author',
    )
    search_fields = (
        'user',
        'author',
    )
    list_filter = (
        'user',
        'author',
    )
    empty_value_filter = '-пусто-'


# Регистрируем кастомизированные модели в админке
admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
