from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser

from foodgram_back.settings import (
    MAX_USERNAME_FIRST_LAST_NAME_LENGTH,
    MAX_EMAIL_LENGTH,
)


class User(AbstractUser):
    username = models.CharField(
        "Логин",
        max_length=MAX_USERNAME_FIRST_LAST_NAME_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+\Z",
                message="Строка должна состоять только из символов латиницы, цифр, знака подчеркивания, точки, "
                "собаки, плюса и минуса. В строке должен быть хотя бы один такой символ",
            ),
        ],
    )
    email = models.EmailField(
        "Почта",
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+\Z",
                message="Строка должна состоять только из символов латиницы, цифр, знака подчеркивания, точки, "
                "собаки, плюса и минуса. В строке должен быть хотя бы один такой символ",
            ),
        ],
    )
    first_name = models.CharField(
        "Имя", max_length=MAX_USERNAME_FIRST_LAST_NAME_LENGTH
    )
    last_name = models.CharField(
        "Фамилия", max_length=MAX_USERNAME_FIRST_LAST_NAME_LENGTH
    )
    avatar = models.ImageField(
        "Аватар", upload_to="users/", null=True, default="userpic-icon.jpg"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "password"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
        related_name="subscriptions",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="followers",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подпики"
        ordering = ("subscriber",)
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber", "author"],
                name="unique_subscriber_author",
            ),
        ]

    def __str__(self):
        return f"{self.subscriber} подписан на {self.author}"
