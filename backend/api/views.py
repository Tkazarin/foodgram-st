from io import BytesIO

from django.core.files.storage import default_storage
from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet as AuthUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.filters import CustomRecipeFilter, CustomIngredientFilter
from api.pagination import CustomPagination
from api.permission import IsAuthorOrReadOnly
from recipes.models import (
    Favorite,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)
from ingredients.models import Ingredient
from users.models import User

from api.serializers.ingredients import IngredientSerializer
from api.serializers.recipes import (
    CartSerializer,
    RecipeDetailSerializer,
    RecipeCreateSerializer,
    FavoriteRecipeSerializer,
)
from api.serializers.users import (
    UserAvatarSerializer,
    SubscriptionDetailSerializer,
    SubscriptionCreateSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
)


class UserActionsViewSet(AuthUserViewSet):
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegistrationSerializer
        elif self.action == "avatar":
            return UserAvatarSerializer
        elif self.action in ["subscriptions", "subscribe"]:
            if self.request.method == "POST":
                return SubscriptionCreateSerializer
            return SubscriptionDetailSerializer
        return UserDetailSerializer

    @action(detail=False, permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        user = request.user
        if request.method == "DELETE":
            self.delete_avatar(user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(
            user, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"avatar": self.get_avatar_url(request, user)})

    def delete_avatar(self, user):
        if user.avatar:
            if (
                hasattr(user.avatar, "url_path")
                and user.avatar.name != "users/image.png"
            ):
                default_storage.delete(user.avatar.url_path)
            elif user.avatar.name != "users/image.png":
                user.avatar.delete(save=False)
            user.avatar = None
            user.save()

    def get_avatar_url(self, request, user):
        return (
            request.build_absolute_uri(user.avatar.url)
            if user.avatar
            else None
        )

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="subscriptions",
    )
    def subscriptions(self, request):
        authors = User.objects.filter(
            id__in=request.user.subscriptions.values("author")
        )
        page = self.paginate_queryset(authors)
        serializer = self.get_serializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["POST", "DELETE"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, pk=None, id=None):
        author_id = id if id is not None else pk
        author = get_object_or_404(User, pk=author_id)

        if request.method == "POST":
            return self.create_subscription(request, author)
        else:
            return self.delete_subscription(request, author)

    def create_subscription(self, request, author):
        serializer = self.get_serializer(
            data={"subscriber": request.user.id, "author": author.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_subscription(self, request, author):
        deleted, _ = request.user.subscriptions.filter(author=author).delete()
        if not deleted:
            return Response(
                {"errors": "Вы не подписаны на этого автора."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="set_password",
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeAPIViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CustomRecipeFilter

    def initialize_recipe_creation(self, serializer):
        serializer.save(created_by=self.request.user)

    def manage_user_interaction(
        self,
        req,
        recipe_id,
        relation_model,
        response_serializer,
        duplicate_message,
    ):
        current_user = req.user
        target_recipe = get_object_or_404(Recipe, id=recipe_id)

        if req.method == "POST":
            return self.add_relation(
                current_user,
                target_recipe,
                relation_model,
                response_serializer,
                duplicate_message,
                req,
            )
        else:
            return self.remove_relation(
                current_user, recipe_id, relation_model
            )

    def add_relation(
        self, user, recipe, model, serializer_class, error_msg, request
    ):
        if model.objects.filter(recipe=recipe, user=user).exists():
            return Response(
                {"message": error_msg.format(recipe.name)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serialized_data = serializer_class(
            data={"recipe": recipe.id, "user": user.id},
            context={"request": request},
        )
        serialized_data.is_valid(raise_exception=True)
        serialized_data.save()
        return Response(serialized_data.data, status=status.HTTP_201_CREATED)

    def remove_relation(self, user, recipe_id, model):
        removal_result = model.objects.filter(
            recipe__id=recipe_id, user=user
        ).delete()

        if removal_result[0] > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"error": "Рецепт не найден в вашем списке"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        methods=["POST", "DELETE"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="favorite",
        url_name="favorite",
    )
    def bookmark_recipe(self, request, pk=None):
        return self.manage_user_interaction(
            req=request,
            recipe_id=pk,
            relation_model=Favorite,
            response_serializer=FavoriteRecipeSerializer,
            duplicate_message='Рецепт "{}" уже в ваших закладках.',
        )

    @action(
        methods=["POST", "DELETE"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="shopping_cart",
        url_name="shopping_cart",
    )
    def manage_cart(self, request, pk=None):
        return self.manage_user_interaction(
            req=request,
            recipe_id=pk,
            relation_model=ShoppingCart,
            response_serializer=CartSerializer,
            duplicate_message='Рецепт "{}" уже в вашей корзине.',
        )

    def get_serializer_class(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return RecipeDetailSerializer
        return RecipeCreateSerializer

    def get_queryset(self):
        queryset = Recipe.objects.select_related("author").prefetch_related(
            "ingredient", "recipe_ingredients", "shopping_carts", "favorites"
        )
        if self.request.user.is_authenticated:
            user = self.request.user
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef("pk"))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef("pk")
                    )
                ),
            )

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
        url_name="download_shopping_cart",
    )
    def export_ingredients(self, request):
        ingredient_data = self.compile_ingredient_data(request.user)
        file_content = self.create_shopping_list_file(ingredient_data)
        return self.send_file_response(file_content)

    def compile_ingredient_data(self, user):
        return (
            RecipeIngredient.objects.filter(recipe__shopping_carts__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

    def create_shopping_list_file(self, ingredients):
        list_content = "\n".join(
            f'{item["ingredient__name"]} - {item["total_amount"]} {item["ingredient__measurement_unit"]}'
            for item in ingredients
        )
        file_buffer = BytesIO()
        file_buffer.write(list_content.encode("utf-8"))
        file_buffer.seek(0)
        return file_buffer

    def send_file_response(self, file_buffer):
        response = HttpResponse(
            file_buffer, content_type="text/plain; charset=utf-8"
        )
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        methods=["GET"],
        detail=True,
        permission_classes=[AllowAny],
        url_path="get-link",
        url_name="get-link",
    )
    def generate_shareable_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        link_path = reverse("short_url", args=[recipe.pk])
        return Response(
            {"short-link": request.build_absolute_uri(link_path)},
            status=status.HTTP_200_OK,
        )


def handle_shortlink(request, short_link):
    try:
        recipe_id = int(short_link)
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        return redirect("api:recipe-detail", pk=recipe.id)
    except ValueError:
        raise ValueError("Invalid short link")


class IngredientAPIViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CustomIngredientFilter
    search_fields = ("^name",)
