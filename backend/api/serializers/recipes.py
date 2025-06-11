from rest_framework import serializers

from ingredients.models import Ingredient
from recipes.models import RecipeIngredient, Recipe, ShoppingCart, Favorite

from api.serializers.general import Base64EncodedImageField
from api.serializers.users import (
    UserDetailSerializer,
    RecipeMiniDisplaySerializer,
)


from foodgram_back.settings import (
    MIN_COOKING_TIME, MAX_COOKING_TIME,
    MAX_INGREDIENT_AMOUNT, MIN_INGREDIENT_AMOUNT
)


class RecipeIngredientDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT, max_value=MAX_INGREDIENT_AMOUNT,
        error_messages={
            "min_value":
                f"Количество должно быть не менее {MIN_INGREDIENT_AMOUNT}.",
            "max_value":
                f"Количество не может превышать {MAX_INGREDIENT_AMOUNT}."
        }
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeDetailSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)
    ingredients = RecipeIngredientDetailSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    image = Base64EncodedImageField(required=True, allow_null=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def _relation_exists(self, recipe_obj, relation_model):
        request = self.context.get("request")
        if (
            not request
            or not hasattr(request, "user")
            or not request.user.is_authenticated
        ):
            return False
        return relation_model.objects.filter(
            recipe=recipe_obj, user=request.user
        ).exists()

    def get_is_favorited(self, recipe_obj):
        return self._relation_exists(recipe_obj, Favorite)

    def get_is_in_shopping_cart(self, recipe_obj):
        return self._relation_exists(recipe_obj, ShoppingCart)


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field="username", read_only=True
    )
    ingredients = RecipeIngredientCreateSerializer(
        many=True, source="recipe_ingredients"
    )
    image = Base64EncodedImageField(required=True, file_prefix="recipe")
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME, max_value=MAX_COOKING_TIME,
        error_messages={
            "min_value":
                f"Время готовки не может быть меньше "
                f"{MIN_COOKING_TIME} минуты.",
            "max_value":
                f"Время готовки не может превышать "
                f"{MAX_COOKING_TIME} минут."
        }
    )

    class Meta:
        model = Recipe
        fields = (
            "author",
            "ingredients",
            "image",
            "name",
            "text",
            "cooking_time",
        )
        read_only_fields = ("author",)

    def validate(self, data):
        ingredient_list = data.get("recipe_ingredients", [])
        if not ingredient_list:
            raise serializers.ValidationError(
                {"ingredients": [{"id": "Обязательное поле."}]}
            )

        ingredient_ids = [
            item.get("ingredient").id for item in ingredient_list
        ]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты должны быть уникальными."}
            )

        errors = []

        if errors:
            raise serializers.ValidationError({"ingredients": errors})

        return data

    def create_ingredients(self, recipe, ingredient_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient["ingredient"],
                amount=ingredient["amount"],
            )
            for ingredient in ingredient_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredient_data = validated_data.pop("recipe_ingredients")
        user = self.context["request"].user

        validated_data.pop("author", None)

        recipe = Recipe.objects.create(author=user, **validated_data)
        self.create_ingredients(recipe, ingredient_data)
        return recipe

    def update(self, instance, validated_data):
        ingredient_data = validated_data.pop("recipe_ingredients")
        instance.recipe_ingredients.all().delete()
        self.create_ingredients(instance, ingredient_data)
        updated_recipe = super().update(instance, validated_data)
        return updated_recipe

    def to_representation(self, instance):
        return RecipeDetailSerializer(
            instance, context={"request": self.context.get("request")}
        ).data


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")

    def validate(self, attrs):
        if ShoppingCart.objects.filter(**attrs).exists():
            raise serializers.ValidationError(
                "Этот рецепт уже добавлен в корзину."
            )
        return attrs

    def to_representation(self, instance):
        return RecipeMiniDisplaySerializer(
            instance.recipe, context={"request": self.context.get("request")}
        ).data


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ("user", "recipe")

    def validate(self, attrs):
        if Favorite.objects.filter(**attrs).exists():
            raise serializers.ValidationError(
                "Этот рецепт уже добавлен в избранное."
            )
        return attrs

    def to_representation(self, instance):
        return RecipeMiniDisplaySerializer(instance.recipe).data
