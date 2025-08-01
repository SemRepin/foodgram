from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from recipes.models import Tag

User = get_user_model()


class Command(BaseCommand):
    """Команда для создания тестовых данных."""

    help = "Создать тестовые данные"

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            _ = User.objects.create_superuser(
                username="admin",
                email="admin@foodgram.com",
                password="admin123",
                first_name="Админ",
                last_name="Админов",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Создан суперпользователь: admin@foodgram.com/admin123"
                )
            )

        if not User.objects.filter(username="testuser").exists():
            _ = User.objects.create_user(
                username="testuser",
                email="test@foodgram.com",
                password="test123",
                first_name="Тест",
                last_name="Тестов",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Создан тестовый пользователь: test@foodgram.com/test123"
                )
            )

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
