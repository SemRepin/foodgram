import base64

from django.core.files.base import ContentFile
from django.core.validators import EmailValidator, RegexValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from .constants import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH, USERNAME_MAX_LENGTH
from .models import Follow, User


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки изображений в base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)
        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    email = serializers.EmailField(
        required=True,
        max_length=EMAIL_MAX_LENGTH,
        validators=[EmailValidator(message="Некорректный email")],
    )
    username = serializers.CharField(
        required=True,
        max_length=USERNAME_MAX_LENGTH,
        validators=[
            RegexValidator(
                r"^[\w.@+-]+$", "Недопустимые символы в имени пользователя"
            )
        ],
    )
    first_name = serializers.CharField(
        required=True, max_length=NAME_MAX_LENGTH
    )
    last_name = serializers.CharField(
        required=True, max_length=NAME_MAX_LENGTH
    )
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "password")

    def validate_email(self, value):
        """Проверить уникальность email."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value

    def validate_username(self, value):
        """Проверить уникальность username."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким username уже существует."
            )
        return value

    def create(self, validated_data):
        """Создать нового пользователя."""
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        """Возвращает данные созданного пользователя без пароля."""
        return {
            "email": instance.email,
            "id": instance.id,
            "username": instance.username,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
        }


class CustomUserSerializer(UserSerializer):
    """Сериализатор для пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_avatar(self, obj):
        """Получить URL аватара пользователя."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_is_subscribed(self, obj):
        """Проверить подписку на пользователя."""
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return False

        user = request.user
        if not user or user.is_anonymous:
            return False

        return self._is_user_subscribed_to_author(user, obj)

    def _is_user_subscribed_to_author(self, user, author):
        """Проверить подписку пользователя на автора."""
        return Follow.objects.filter(user=user, author=author).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ("avatar",)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для рецепта (используется в подписках)."""

    class Meta:
        from recipes.models import Recipe
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_avatar(self, obj):
        """Получить URL аватара автора (если есть)."""
        if obj.author.avatar:
            return obj.author.avatar.url
        return None

    def get_is_subscribed(self, obj):
        """Проверить подписку."""
        return True

    def get_recipes(self, obj):
        """Получить рецепты автора."""
        from recipes.models import Recipe
        
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        recipes = Recipe.objects.filter(author=obj.author)
        if limit:
            try:
                limit = int(limit)
                recipes = recipes[:limit]
            except (ValueError, TypeError):
                pass
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Получить количество рецептов автора."""
        from recipes.models import Recipe
        return Recipe.objects.filter(author=obj.author).count()
