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

    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(
        required=True, min_value=MIN_INGREDIENTS_COUNT
    )

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

    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True
    )
    image = Base64ImageField(required=True)
    name = serializers.CharField(required=True, max_length=RECIPE_MAX_LENGTH)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(
        required=True, min_value=MIN_COOKING_TIME
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

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Название рецепта не может быть пустым."
            )
        return value.strip()

    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Описание рецепта не может быть пустым."
            )
        return value.strip()

    def validate_cooking_time(self, value):
        if value < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                "Время приготовления должно быть больше либо равно "
                f"{MIN_COOKING_TIME}."
            )
        return value

    def validate_image(self, value):
        if not value or value == "":
            raise serializers.ValidationError(
                "Изображение рецепта обязательно."
            )
        return value

    def validate_ingredients(self, value):
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
                    "Количество ингредиента должно быть больше либо равно "
                    f"{MIN_INGREDIENTS_COUNT}."
                )

        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError("Нужен хотя бы один тег.")

        if len(value) != len(set(value)):
            raise serializers.ValidationError("Теги не должны повторяться.")

        return value

    def validate(self, data):
        """Общая валидация данных (для update)."""
        if self.instance:
            required_fields = {
                "name": "Название рецепта обязательно.",
                "text": "Описание рецепта обязательно.",
                "cooking_time": "Время приготовления обязательно.",
                "image": "Изображение рецепта обязательно.",
                "ingredients": "Ингредиенты обязательны.",
                "tags": "Теги обязательны.",
            }

            for field, error_message in required_fields.items():
                if field not in self.initial_data:
                    raise serializers.ValidationError({field: error_message})
        return data

    def create_recipe_ingredients(self, recipe, ingredients_data):
        """Создать ингредиенты для рецепта."""
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data["id"],
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
