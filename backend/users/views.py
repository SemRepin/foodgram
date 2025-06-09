from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.pagination import LimitPageNumberPagination

from .models import Follow, User
from .serializers import (
    AvatarSerializer, CustomUserCreateSerializer, CustomUserSerializer,
    FollowSerializer,
)

CREATED = status.HTTP_201_CREATED
NO_CONTENT = status.HTTP_204_NO_CONTENT
BAD_REQUEST = status.HTTP_400_BAD_REQUEST


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
            return self.handle_subscribe(user, author, request)
        elif request.method == "DELETE":
            return self.handle_unsubscribe(user, author)

    def handle_subscribe(self, user, author, request):
        """Обработать подписку на автора."""
        if user == author:
            return Response(
                {"errors": "Нельзя подписаться на самого себя"},
                status=BAD_REQUEST,
            )
        if self._is_user_subscribed_to_author(user, author):
            return Response(
                {"errors": "Вы уже подписаны на этого пользователя"},
                status=BAD_REQUEST,
            )

        follow = Follow.objects.create(user=user, author=author)
        serializer = FollowSerializer(follow, context={"request": request})
        return Response(serializer.data, status=CREATED)

    def handle_unsubscribe(self, user, author):
        """Обработать отписку от автора."""
        follow = Follow.objects.filter(user=user, author=author)
        if follow.exists():
            follow.delete()
            return Response(status=NO_CONTENT)
        return Response(
            {"errors": "Вы не подписаны на этого пользователя"},
            status=BAD_REQUEST,
        )

    def _is_user_subscribed_to_author(self, user, author):
        """Проверить подписку пользователя на автора."""
        return Follow.objects.filter(user=user, author=author).exists()

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
            return self.handle_avatar_update(user, request)
        elif request.method == "DELETE":
            return self.handle_avatar_delete(user)

    def handle_avatar_update(self, user, request):
        """Обработать обновление аватара."""
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

    def handle_avatar_delete(self, user):
        """Обработать удаление аватара."""
        user.avatar.delete()
        user.save()
        return Response(status=NO_CONTENT)
