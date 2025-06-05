from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, CustomUserCreateSerializer,
                          CustomUserSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeListSerializer, RecipeShortSerializer,
                          TagSerializer)

CREATED = status.HTTP_201_CREATED
NO_CONTENT = status.HTTP_204_NO_CONTENT
BAD_REQUEST = status.HTTP_400_BAD_REQUEST
NOT_FOUND = status.HTTP_404_NOT_FOUND


class CustomUserViewSet(UserViewSet):
    """ViewSet для пользователей."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        if self.action == "create":
            return CustomUserCreateSerializer
        elif self.action == "set_password":
            return SetPasswordSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [AllowAny]
        elif self.action in ["retrieve", "list"]:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        else:
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получить список подписок пользователя."""
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, **kwargs):
        """Подписаться/отписаться от автора."""
        user = request.user
        author_id = self.kwargs.get("id")
        author = get_object_or_404(User, id=author_id)

        if request.method == "POST":
            if user == author:
                return Response(
                    {"errors": "Нельзя подписаться на самого себя"},
                    status=BAD_REQUEST,
                )
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя"},
                    status=BAD_REQUEST,
                )

            follow = Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(follow, context={"request": request})
            return Response(serializer.data, status=CREATED)

        if request.method == "DELETE":
            follow = Follow.objects.filter(user=user, author=author)
            if follow.exists():
                follow.delete()
                return Response(status=NO_CONTENT)
            return Response(
                {"errors": "Вы не подписаны на этого пользователя"},
                status=BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        """Обновить или удалить аватар пользователя."""
        user = request.user

        if request.method == "PUT":
            if "avatar" not in request.data:
                return Response(
                    {"avatar": ["Это поле обязательно."]}, status=BAD_REQUEST
                )

            serializer = AvatarSerializer(
                user,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        if request.method == "DELETE":
            user.avatar.delete()
            user.save()
            return Response(status=NO_CONTENT)


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
        """Получить класс сериализатора."""
        if self.action in ["list", "retrieve"]:
            return RecipeListSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        """Создать рецепт."""
        serializer.save(author=self.request.user)

    # def get_recipe_id(self, request, **kwargs):

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
        """Добавить или удалить рецепт."""
        user = request.user
        recipe_id = self.kwargs.get("pk")
        recipe = get_object_or_404(Recipe, id=recipe_id)

        if request.method == "POST":
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже добавлен"}, status=BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=CREATED)

        if request.method == "DELETE":
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

        ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping_cart__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        shopping_list = "Список покупок:\n\n"
        for ingredient in ingredients:
            shopping_list += (
                f"• {ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) — "
                f"{ingredient['total_amount']}\n"
            )

        response = HttpResponse(shopping_list, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

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
