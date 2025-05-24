from rest_framework import serializers

from users.models import User, Subscription
from recipes.models import Recipe

from api.serializers.general import Base64EncodedImageField


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64EncodedImageField(allow_null=True, file_prefix="avatar")

    class Meta:
        model = User
        fields = ["avatar"]


class UserDetailSerializer(serializers.ModelSerializer):
    avatar = Base64EncodedImageField(
        allow_null=True, required=False, file_prefix="avatar"
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
        ]

    def get_is_subscribed(self, user_obj):
        request_user = self.context.get("request").user
        if request_user.is_authenticated:
            return user_obj.followers.filter(subscriber=request_user).exists()
        return False


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(default=0)
    is_subscribed = serializers.BooleanField(default=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "recipes",
            "recipes_count",
            "avatar",
            "is_subscribed",
        )

    def get_recipes(self, author):
        request = self.context.get("request")
        author_recipes = author.recipes.all()
        limit = request.GET.get("recipes_limit")
        if limit and limit.isdigit():
            author_recipes = author_recipes[: int(limit)]
        return RecipeMiniDisplaySerializer(
            author_recipes, many=True, context={"request": request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ("subscriber", "author")

    def validate_author(self, author):
        current_user = self.context["request"].user
        if current_user == author:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя."
            )
        if Subscription.objects.filter(
            subscriber=current_user, author=author
        ).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого автора."
            )
        return author

    def to_representation(self, instance):
        request = self.context.get("request")
        return SubscriptionDetailSerializer(
            instance.author, context={"request": request}
        ).data


class RecipeMiniDisplaySerializer(serializers.ModelSerializer):
    image = Base64EncodedImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )
