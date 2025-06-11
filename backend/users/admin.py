from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    search_fields = ("username", "email")
    search_help_text = "Поиск по имени пользователя или email"
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")
    ordering = ("username",)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):

    list_display = ("user", "author")
    search_fields = (
        "user__username",
        "author__username",
        "user__email",
        "author__email",
    )
    search_help_text = "Поиск по имени пользователя или email"
    list_filter = ("user", "author")
