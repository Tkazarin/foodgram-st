from django.contrib import admin
from django.utils.safestring import mark_safe

from recipes.models import (
    Favorite,
    Recipe,
    ShoppingCart,
    RecipeIngredient,
)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    class RecipeIngredientInline(admin.TabularInline):
        model = RecipeIngredient
        extra = 0

    list_display = (
        "name",
        "author",
        "text",
        "cooking_time",
        "image_display",
        "created_at",
    )
    search_fields = ("name",)
    list_filter = (
        "author__username",
        "created_at",
    )
    inlines = (RecipeIngredientInline,)

    @admin.display(description="Картинка")
    def image_display(self, recipe):
        if recipe.image and hasattr(recipe.image, "url"):
            return mark_safe(
                f'<img src="{recipe.image.url}" style="max-width: 70px; '
                f'max-height: 70px; object-fit: cover;" />'
            )
        return "Нет изображения"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("author").prefetch_related(
            "recipe_ingredients__ingredient"
        )
        return queryset


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("user", "recipe__author")
        return queryset


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("user", "recipe__author")
        return queryset


admin.site.empty_value_display = "Отсутствует"
