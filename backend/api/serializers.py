from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import (
    MIN_COOKING_TIME, MIN_INGREDIENTS_COUNT, RECIPE_MAX_LENGTH,
)
from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
)
from users.serializers import CustomUserSerializer


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

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        error_messages={
            "required": "Укажите id ингредиента.",
            "does_not_exist": "Ингредиент не найден!",
        },
    )
    amount = serializers.IntegerField(
        required=True,
        min_value=MIN_INGREDIENTS_COUNT,
        error_messages={
            "required": "Необходимо указать количество ингредиента.",
            "min_value": (
                "Количество ингредиента должно быть больше либо равно "
                f"{MIN_INGREDIENTS_COUNT}."
            ),
        },
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(read_only=True)

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

    ingredients = RecipeIngredientCreateSerializer(
        many=True,
        required=True,
        allow_empty=False,
        error_messages={
            "required": "Ингредиенты обязательны.",
            "empty": "Необходимо указать хотя бы один ингредиент.",
        },
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        allow_empty=False,
        error_messages={
            "required": "Теги обязательны.",
            "empty": "Необходимо указать хотя бы один тег.",
            "does_not_exist": "Тег не найден!",
        },
    )
    image = Base64ImageField(
        required=True,
        error_messages={
            "required": "Изображение рецепта обязательно.",
        },
    )
    name = serializers.CharField(
        required=True,
        max_length=RECIPE_MAX_LENGTH,
        error_messages={
            "required": "Название рецепта обязательно.",
            "blank": "Название рецепта не может быть пустым.",
        },
    )
    text = serializers.CharField(
        required=True,
        error_messages={
            "required": "Описание рецепта обязательно.",
            "blank": "Описание рецепта не может быть пустым.",
        },
    )
    cooking_time = serializers.IntegerField(
        required=True,
        min_value=MIN_COOKING_TIME,
        error_messages={
            "required": "Время приготовления обязательно.",
            "min_value": (
                "Время приготовления должно быть больше либо равно "
                f"{MIN_COOKING_TIME}."
            ),
        },
    )

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

    def validate_ingredients(self, value):
        ingredient_ids = [item["id"].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        return value

    def validate_tags(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Теги не должны повторяться.")
        return value

    def validate_image(self, value):
        if value is None or value == "":
            raise serializers.ValidationError(
                "Изображение рецепта обязательно и не может быть пустым."
            )
        return value

    def validate(self, data):
        """Валидация для обновления рецепта без полей tags, ingredients и/или image."""
        if self.instance:
            for field, error_message in {
                "tags": "Теги обязательны.",
                "ingredients": "Ингредиенты обязательны.",
            }.items():
                if field not in self.initial_data:
                    raise serializers.ValidationError({field: error_message})
            if not self.instance.image and "image" not in self.initial_data:
                raise serializers.ValidationError(
                    {"image": "Изображение рецепта обязательно."}
                )
        return data

    def create_recipe_ingredients(self, recipe, ingredients_data):
        """Создать ингредиенты для рецепта."""
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data["id"],
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        """Создать рецепт."""
        ingredients_data = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновить рецепт."""
        ingredients_data = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.create_recipe_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data
