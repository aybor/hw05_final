from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    """Кастомизация админки для постов."""

    # вбираем отображаемые поля.
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    # Указываем, что поиск будет осуществляться по полю "текст"
    search_fields = ('text',)
    # Фильтрация будет доступна по дате публикации
    list_filter = ('pub_date',)
    # Принадлежность к группе можно редактировать сразу из списка постов
    list_editable = ('group',)
    # если любое из полей не заполнено, на его месте будет -пусто-
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    """Кастомизация админки для групп."""

    # Выбираем отображаемые поля
    list_display = (
        'pk',
        'title',
        'description',
        'slug'
    )
    # поиск будет проводиться по полю "описание"
    search_fields = 'description',
    # на месте пустого поля будет -пусто-
    empty_value_key = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    """Кастомизайия админки для комментов"""

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
    """Кастомизация админки для подписок"""

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
