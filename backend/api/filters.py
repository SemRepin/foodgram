from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = filters.CharFilter(lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ["name"]


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.CharFilter(method="filter_tags")
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ["tags", "author", "is_favorited", "is_in_shopping_cart"]

    def filter_tags(self, queryset, name, value):
        """Фильтр по тегам."""
        if not value:
            return queryset

        if hasattr(self.request, "query_params"):
            tags_list = self.request.query_params.getlist("tags")
        else:
            tags_list = [value]

        if tags_list:
            return queryset.filter(tags__slug__in=tags_list).distinct()

        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """Фильтр по избранному."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтр по списку покупок."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset
