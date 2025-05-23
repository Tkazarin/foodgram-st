from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from .models import User, Subscription


class SimpleHasRelationFilter(admin.SimpleListFilter):
    relation_field = None
    title = ""
    parameter_name = ""

    def lookups(self, request, model_admin):
        return (
            ("has", self.title),
        )

    def queryset(self, request, queryset):
        if self.value() == "has":
            return queryset.filter(**{f"{self.relation_field}__isnull": False}).distinct()
        return queryset

class UserHasRecipesFilter(SimpleHasRelationFilter):
    title = _("есть рецепты")
    parameter_name = "has_recipes"
    relation_field = "recipes"

class UserHasSubscriptionsFilter(SimpleHasRelationFilter):
    title = _("есть подписки")
    parameter_name = "has_subscriptions"
    relation_field = "subscriptions"

class UserHasSubscribersFilter(SimpleHasRelationFilter):
    title = _("есть подписчики")
    parameter_name = "has_subscribers"
    relation_field = "subscribers"


@admin.register(User)
class CustUserAdmin(UserAdmin):
    list_display = (
        'id',
        'username',
        'get_full_name',
        'email',
        'get_subscribers',
        'get_subscriptions',
        'get_recipes_count',
        'get_recipes',
        'get_avatar',
    )
    search_fields = ("email", "username", "first_name", "last_name")
    list_filter = (
        "is_staff",
        "is_active",
        UserHasRecipesFilter,
        UserHasSubscriptionsFilter,
        UserHasSubscribersFilter,
    )
    ordering = ("username",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name",
                                      "last_name", "email", "avatar")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff",
                        "is_superuser")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )

    @admin.display(description='Количество рецептов')
    def get_recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Количество подписок')
    def get_subscriptions(self, user):
        return user.subscriptions.count()

    @admin.display(description='Количество подписчиков')
    def get_subscribers(self, user):
        return user.followers.count()

    @admin.display(description='Количество рецептов')
    def get_recipes(self, user):
        return user.recipes.count()

    @admin.display(description="Фамилия Имя")
    def get_full_name(self, user):
        return f"{user.first_name} {user.last_name}"

    @admin.display(description="Аватар")
    def get_avatar(self, user):
        if user.avatar:
            return mark_safe(f'<img src="{user.avatar.url}" width="50" height="50" />')
        return "Нет аватара"

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('author', 'subscriber')
    search_fields = ('author__username', 'subscriber__username')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('author', 'subscriber')
        return queryset

admin.site.empty_value_display = 'Отсутствует'