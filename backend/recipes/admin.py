from django.contrib import admin

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
)


class RecipeIngredientInline(admin.TabularInline):

    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):

    list_display = ("name", "slug")
    search_fields = ("name",)
    search_help_text = "Поиск по тегу"
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):

    list_display = ("name", "measurement_unit")
    search_fields = ("name",)
    search_help_text = "Поиск по ингредиенту"
    list_filter = ("measurement_unit",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):

    list_display = ("name", "author", "get_favorites_count")
    search_fields = ("name", "author__username")
    search_help_text = "Поиск по названию рецепта или автору"
    list_filter = ("tags", "pub_date")
    inlines = (RecipeIngredientInline,)
    filter_horizontal = ("tags",)

    @admin.display(description="В избранном")
    def get_favorites_count(self, obj):
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):

    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):

    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
