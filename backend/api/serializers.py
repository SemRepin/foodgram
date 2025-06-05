import base64

from django.core.files.base import ContentFile
from django.core.validators import EmailValidator, RegexValidator
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.constants import (
    MIN_COOKING_TIME,
    MIN_INGREDIENTS_COUNT,
    RECIPE_MAX_LENGTH,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.constants import (
    EMAIL_MAX_LENGTH,
    NAME_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
)
from users.models import Follow, User


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
    avatar = Base64ImageField(required=False, allow_null=True)

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

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return False

        user = request.user
        if not user or user.is_anonymous:
            return False

        return Follow.objects.filter(user=user, author=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ("avatar",)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов в рецепте."""

    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")

    def validate_amount(self, value):
        if value < MIN_INGREDIENTS_COUNT:
            raise serializers.ValidationError(
                f"Количество должно быть больше либо равно "
                f"{MIN_INGREDIENTS_COUNT}."
            )
        return value


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return False

        user = request.user
        if not user or user.is_anonymous:
            return False

        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return False

        user = request.user
        if not user or user.is_anonymous:
            return False

        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True
    )
    image = Base64ImageField(required=True)
    name = serializers.CharField(required=True, max_length=RECIPE_MAX_LENGTH)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def validate_name(self, value):
        """Валидация названия рецепта."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Название рецепта не может быть пустым."
            )
        return value.strip()

    def validate_text(self, value):
        """Валидация описания рецепта."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Описание рецепта не может быть пустым."
            )
        return value.strip()

    def validate_cooking_time(self, value):
        """Валидация времени приготовления."""
        if value < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                f"Время приготовления должно быть больше либо равно "
                f"{MIN_COOKING_TIME}."
            )
        return value

    def validate_ingredients(self, value):
        """Валидация ингредиентов."""
        if not value:
            raise serializers.ValidationError("Нужен хотя бы один ингредиент.")

        ingredient_ids = [item["id"] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )

        existing_ingredients = Ingredient.objects.filter(id__in=ingredient_ids)
        existing_ids = set(existing_ingredients.values_list("id", flat=True))
        for ingredient_id in ingredient_ids:
            if ingredient_id not in existing_ids:
                raise serializers.ValidationError(
                    f"Ингредиент с id {ingredient_id} не существует."
                )

        for item in value:
            if item["amount"] < MIN_INGREDIENTS_COUNT:
                raise serializers.ValidationError(
                    f"Количество ингредиента должно быть больше либо равно "
                    f"{MIN_INGREDIENTS_COUNT}."
                )

        return value

    def validate_tags(self, value):
        """Валидация тегов."""
        if not value:
            raise serializers.ValidationError("Нужен хотя бы один тег.")

        if len(value) != len(set(value)):
            raise serializers.ValidationError("Теги не должны повторяться.")

        return value

    @transaction.atomic
    def create(self, validated_data):
        """Создать рецепт."""
        ingredients_data = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data["id"],
                amount=ingredient_data["amount"],
            )

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновить рецепт."""
        if "ingredients" not in self.initial_data:
            raise serializers.ValidationError(
                {"ingredients": "Это поле обязательно."}
            )

        if "tags" not in self.initial_data:
            raise serializers.ValidationError(
                {"tags": "Это поле обязательно."}
            )

        ingredients_data = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_data["id"],
                    amount=ingredient_data["amount"],
                )

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для рецепта."""

    class Meta:
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
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        recipes = obj.author.recipes.all()
        if limit:
            try:
                limit = int(limit)
                recipes = recipes[:limit]
            except (ValueError, TypeError):
                pass
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Получить количество рецептов автора."""
        return obj.author.recipes.count()
