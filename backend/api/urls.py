from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientAPIViewSet,
    RecipeAPIViewSet,
    UserActionsViewSet,
)

app_name = "api"

router = DefaultRouter()

router.register("users", UserActionsViewSet, basename="user")
router.register("recipes", RecipeAPIViewSet, basename="recipe")
router.register("ingredients", IngredientAPIViewSet, basename="ingredient")

urlpatterns = [
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
