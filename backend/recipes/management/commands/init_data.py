from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Команда для инициализации всех начальных данных."""

    help = (
        "Загрузить все начальные данные "
        "(теги, ингредиенты, тестовые пользователи)"
    )

    def handle(self, *args, **options):
        self.stdout.write("Начинаем загрузку данных...")

        self.stdout.write("Загружаем ингредиенты...")
        call_command('load_ingredients')

        self.stdout.write("Создаем тестовые данные...")
        call_command('create_test_data')

        self.stdout.write(self.style.SUCCESS("Все данные успешно загружены!"))
