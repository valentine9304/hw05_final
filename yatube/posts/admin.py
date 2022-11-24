from django.contrib import admin

# Register your models here.
from .models import Group, Post, Comment, Follow


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'text',
        'author',
        'created',
    )

class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author',
    )


# При регистрации модели Post источником конфигурации для неё назначаем
# класс PostAdmin
admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Comment, CommentAdmin)
