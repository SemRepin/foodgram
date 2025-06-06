from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
)
from users.serializers import RecipeShortSerializer

from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer, RecipeCreateSerializer, RecipeListSerializer,
    TagSerializer,
)

CREATED = status.HTTP_201_CREATED
NO_CONTENT = status.HTTP_204_NO_CONTENT
BAD_REQUEST = status.HTTP_400_BAD_REQUEST
NOT_FOUND = status.HTTP_404_NOT_FOUND


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filterset_class = RecipeFilter
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeListSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, **kwargs):
        """Добавить/удалить рецепт из избранного."""
        return self._add_or_remove_recipe(request, Favorite)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, **kwargs):
        """Добавить/удалить рецепт из списка покупок."""
        return self._add_or_remove_recipe(request, ShoppingCart)

    def _add_or_remove_recipe(self, request, model):
        """Добавить или удалить рецепт из коллекции."""
        user = request.user
        recipe_id = self.kwargs.get("pk")
        recipe = get_object_or_404(Recipe, id=recipe_id)

        if request.method == "POST":
            return self._handle_add_recipe(user, recipe, model)
        elif request.method == "DELETE":
            return self._handle_remove_recipe(user, recipe, model)

    def _handle_add_recipe(self, user, recipe, model):
        """Обработать добавление рецепта в коллекцию."""
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"errors": "Рецепт уже добавлен"}, status=BAD_REQUEST
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=CREATED)

    def _handle_remove_recipe(self, user, recipe, model):
        """Обработать удаление рецепта из коллекции."""
        obj = model.objects.filter(user=user, recipe=recipe)
        if obj.exists():
            obj.delete()
            return Response(status=NO_CONTENT)
        return Response({"errors": "Рецепт не найден"}, status=BAD_REQUEST)

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)

        if not shopping_cart.exists():
            return Response(
                {"errors": "Список покупок пуст"}, status=BAD_REQUEST
            )

        ingredients = self._get_shopping_cart_ingredients(user)
        shopping_list = self._format_shopping_list(ingredients)

        response = HttpResponse(shopping_list, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    def _get_shopping_cart_ingredients(self, user):
        """Получить ингредиенты из списка покупок с общим количеством."""
        return (
            RecipeIngredient.objects.filter(recipe__shopping_cart__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

    def _format_shopping_list(self, ingredients):
        """Форматировать список покупок."""
        shopping_list = "Список покупок:\n\n"
        for ingredient in ingredients:
            shopping_list += (
                f"• {ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) — "
                f"{ingredient['total_amount']}\n"
            )
        return shopping_list

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, **kwargs):
        """Получить короткую ссылку на рецепт."""
        recipe_id = self.kwargs.get("pk")

        try:
            Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({"errors": "Рецепт не найден"}, status=NOT_FOUND)

        short_link = (
            f"{request.build_absolute_uri('/').rstrip('/')}/s/{recipe_id}/"
        )
        return Response({"short-link": short_link})

    @action(
        detail=True,
        methods=["get"],
        url_path="redirect",
        permission_classes=[AllowAny],
    )
    def redirect_to_recipe(self, request, **kwargs):
        """Редирект по короткой ссылке на страницу рецепта."""
        recipe_id = self.kwargs.get("pk")
        return redirect(f"/recipes/{recipe_id}/")
