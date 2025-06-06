from django.core.validators import MinValueValidator
from django.db import models

from users.models import User

from .constants import (
    INGREDIENT_MAX_LENGTH, MEASUREMENT_UNIT_MAX_LENGTH, MIN_COOKING_TIME,
    MIN_INGREDIENTS_COUNT, RECIPE_MAX_LENGTH, TAG_MAX_LENGTH,
)


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        "Название",
        max_length=TAG_MAX_LENGTH,
        unique=True,
        help_text=(
            f"Название тега не должно превышать {TAG_MAX_LENGTH} символов"
        ),
    )
    slug = models.SlugField(
        "Слаг",
        max_length=TAG_MAX_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        "Название",
        max_length=INGREDIENT_MAX_LENGTH,
        help_text=(
            f"Название ингредиента не должно превышать "
            f"{INGREDIENT_MAX_LENGTH} символов"
        ),
    )
    measurement_unit = models.CharField(
        "Единица измерения",
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        help_text=(
            f"Единица измерения не должна превышать "
            f"{MEASUREMENT_UNIT_MAX_LENGTH} символов"
        ),
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(
        "Название",
        max_length=RECIPE_MAX_LENGTH,
        help_text=(
            f"Название рецепта не должно превышать "
            f"{RECIPE_MAX_LENGTH} символов"
        ),
    )
    image = models.ImageField(
        "Картинка", upload_to="recipes/images/", null=True, default=None
    )
    text = models.TextField(
        "Описание",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги",
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления (в минутах)",
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=(
                    f"Время приготовления не может быть меньше "
                    f"{MIN_COOKING_TIME} минут"
                ),
            )
        ],
    )
    pub_date = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-pub_date"]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингредиента с количеством."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        validators=[
            MinValueValidator(
                MIN_INGREDIENTS_COUNT,
                message=(
                    f"Количество ингредиентов не может быть меньше "
                    f"{MIN_INGREDIENTS_COUNT}"
                ),
            )
        ],
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            )
        ]

    def __str__(self):
        return f"{self.ingredient} в {self.recipe}"


class Favorite(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user} добавил в избранное {self.recipe}"


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Список покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart"
            )
        ]

    def __str__(self):
        return f"{self.user} добавил в покупки {self.recipe}"
