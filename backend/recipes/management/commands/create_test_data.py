from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from recipes.models import Tag, Recipe, RecipeIngredient, Ingredient

User = get_user_model()


class Command(BaseCommand):
    """Команда для создания тестовых данных."""

    help = "Создать тестовые данные"

    def handle(self, *args, **options):
        # Создаем суперпользователя
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin",
                email="admin@foodgram.com",
                password="admin123",
                first_name="Админ",
                last_name="Админов",
            )
            self.stdout.write(
                self.style.SUCCESS("Создан суперпользователь: admin/admin123")
            )

        # Создаем тестового пользователя
        if not User.objects.filter(username="testuser").exists():
            user = User.objects.create_user(
                username="testuser",
                email="test@foodgram.com",
                password="test123",
                first_name="Тест",
                last_name="Тестов",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Создан тестовый пользователь: testuser/test123"
                )
            )

        # Создаем теги
        tags_data = [
            {"name": "Завтрак", "slug": "breakfast"},
            {"name": "Обед", "slug": "lunch"},
            {"name": "Ужин", "slug": "dinner"},
            {"name": "Десерт", "slug": "dessert"},
        ]

        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(**tag_data)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Создан тег: {tag.name}")
                )

        self.stdout.write(
            self.style.SUCCESS("Тестовые данные созданы успешно!")
        )
