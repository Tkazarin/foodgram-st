from django.db import models
from django.contrib.auth import get_user_model

from foodgram_back.settings import MAX_INGREDIENT_NAME_LENGTH, MAX_MEASUREMENT_UNIT_NAME_LENGTH

User = get_user_model()

class Ingredient(models.Model):
    name = models.CharField("Название ингредиента",
                            max_length=MAX_INGREDIENT_NAME_LENGTH, unique=True)
    measurement_unit = models.CharField(
        "Мера веса ингредиента", max_length=MAX_MEASUREMENT_UNIT_NAME_LENGTH)

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"