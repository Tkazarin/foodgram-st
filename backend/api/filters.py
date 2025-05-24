from django_filters.rest_framework import FilterSet, filters
from recipes.models import Recipe
from ingredients.models import Ingredient


class CustomRecipeFilter(FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_by_favorite_status')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_by_cart_status')

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    def get_current_user(self):
        request = self.request
        return request.user if request and request.user.is_authenticated else None

    def filter_by_favorite_status(self, queryset, field_name, should_filter):
        user = self.get_current_user()
        if should_filter and user:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_by_cart_status(self, queryset, field_name, should_filter):
        user = self.get_current_user()
        if should_filter and user:
            return queryset.filter(shopping_carts__user=user)
        return queryset


class CustomIngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']