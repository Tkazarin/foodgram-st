from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from foodgram_back.settings import (
    MIN_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
    MAX_RECIPE_NAME_LENGTH,
    MAX_COOKING_TIME,
    MAX_INGREDIENT_AMOUNT,
)
from users.models import User


class Recipe(models.Model):
    name = models.CharField("Название", max_length=MAX_RECIPE_NAME_LENGTH)
    author = models.ForeignKey(
        User, verbose_name="Автор", on_delete=models.CASCADE
    )
    ingredient = models.ManyToManyField(
        "ingredients.Ingredient",
        through="RecipeIngredient",
        verbose_name="Ингредиенты",
    )
    text = models.TextField("Описание")
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления",
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME)
        ],
    )
    created_at = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True,
    )
    short_link = models.CharField(
        "Короткая ссылка", blank=True, unique=True, null=True
    )
    image = models.ImageField("Изображение", upload_to="recipes/pics/")

    class Meta:
        default_related_name = "recipes"
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name}. Автор: {self.author}"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        "ingredients.Ingredient",
        verbose_name="Ингредиент",
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        validators=[
            MinValueValidator(MIN_INGREDIENT_AMOUNT),
            MaxValueValidator(MAX_INGREDIENT_AMOUNT)
        ]
    )

    class Meta:
        default_related_name = "recipe_ingredients"
        verbose_name = "Ингридиенты рецепта"
        verbose_name_plural = "Ингридиенты рецепта"
        ordering = ("ingredient",)

    def __str__(self):
        return f"Ингридиент {self.ingredient} в количестве {self.amount}."


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name="Рецепт"
    )

    class Meta:
        ordering = ("user",)
        default_related_name = "shopping_carts"
        verbose_name = "Список покупок"
        verbose_name_plural = "Список покупок"
        constraints = [
            models.UniqueConstraint(
                name="shopping_unique",
                fields=["user", "recipe"],
            )
        ]

    def __str__(self):
        return (f"Список покупок нужных инградиентов пользователя {self.user} "
                f"для рецепта {self.recipe}")


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name="Рецепт"
    )

    class Meta:
        ordering = ("user",)
        default_related_name = "favorites"
        verbose_name = "Рецепт в избранном"
        verbose_name_plural = "Рецепты в избранном"
        constraints = [
            models.UniqueConstraint(
                name="favorite_unique",
                fields=["user", "recipe"],
            )
        ]

    def __str__(self):
        return f"Рецепт {self.recipe} в избранном у пользователя {self.user}"
