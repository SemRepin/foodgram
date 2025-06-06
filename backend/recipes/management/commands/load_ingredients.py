import csv
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для загрузки ингредиентов из CSV файла."""

    help = "Загрузить ингредиенты из CSV файла"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            help="Путь к CSV файлу с ингредиентами",
            default="/data/ingredients.csv",
        )

    def handle(self, *args, **options):
        file_path = options["path"]

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Файл {file_path} не найден"))
            return

        ingredients_created = 0
        ingredients_skipped = 0

        with open(file_path, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:
                if len(row) != 2:
                    continue

                name, measurement_unit = row

                ingredient, created = Ingredient.objects.get_or_create(
                    name=name, measurement_unit=measurement_unit
                )

                if created:
                    ingredients_created += 1
                else:
                    ingredients_skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Загрузка завершена. "
                f"Создано: {ingredients_created}, "
                f"Пропущено: {ingredients_skipped}"
            )
        )
