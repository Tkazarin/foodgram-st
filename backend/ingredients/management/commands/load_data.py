import json
from django.core.management.base import BaseCommand
from ...models import Ingredient

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('json_path', type=str, help='Путь к JSON-файлу с ингредиентами')

    def handle(self, *args, **options):
        json_path = options['json_path']
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            new_ingredients = []
            for entry in data:
                exists = Ingredient.objects.filter(
                    name=entry['name'],
                    measurement_unit=entry['measurement_unit']
                ).exists()
                if not exists:
                    new_ingredients.append(Ingredient(**entry))
            Ingredient.objects.bulk_create(new_ingredients)
            self.stdout.write(
                self.style.SUCCESS(f'Добавлено ингредиентов: {len(new_ingredients)}')
            )
        except Exception as err:
            self.stderr.write(self.style.ERROR(f'Ошибка при загрузке: {err}'))
