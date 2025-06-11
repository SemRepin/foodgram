### Данные для админки
Адрес: https://foodgramchik.sytes.net/
Логин: admin@foodgram.com
Пароль: admin123

<img align="right" width="102" height="90" src="frontend/public/favicon.png">

# Foodgram - веб-приложение для публикации рецептов
![](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![](https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white)
![](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![](https://img.shields.io/badge/docker-257bd6?style=for-the-badge&logo=docker&logoColor=white)
![](https://img.shields.io/badge/-ReactJs-61DAFB?style=for-the-badge&logo=react&logoColor=white)
[![Foodgram CI/CD](https://github.com/SemRepin/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/SemRepin/foodgram/actions/workflows/main.yml)

Фудграм — это веб-приложение для обмена кулинарными рецептами. Пользователи могут публиковать собственные рецепты, добавлять понравившиеся в избранное и подписываться на обновления других авторов. Зарегистрированным пользователям доступен удобный сервис «Список покупок», который автоматически формирует перечень необходимых ингредиентов для выбранных блюд. Готовый список можно скачать в виде файла для использования в магазине или на кухне!

![Foodgram](https://res.cloudinary.com/dhw34rp0t/image/upload/v1749399003/Screenshot_2025-06-08_at_5.33.40_PM_exquqm.png)

## Технологии

- **Backend**: Django 3.2, Django REST Framework
- **Frontend**: React (SPA)
- **База данных**: PostgreSQL
- **Веб-сервер**: Nginx
- **Контейнеризация**: Docker, Docker Compose
- **Аутентификация**: Token-based authentication

## Возможности

- Регистрация и аутентификация пользователей
- Публикация рецептов с фотографиями
- Система тегов для категоризации рецептов
- Подписки на авторов
- Добавление рецептов в избранное
- Список покупок с возможностью скачивания
- Фильтрация рецептов по тегам, автору, избранному
- Админ-панель для управления контентом

## Локальная разработка

### Требования

- Python 3.9+
- Node.js (для фронтенда)
- PostgreSQL (опционально, можно использовать SQLite для тестирования)

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/SemRepin/foodgram.git
cd foodgram
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. Создайте файл `.env` в папке `foodgram/`:
```
SECRET_KEY=your-secret-key
DEBUG=True
USE_SQLITE=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

4. Выполните миграции:
```bash
python manage.py migrate
```

5. Загрузите ингредиенты:
```bash
python manage.py load_ingredients
```

6. Создайте тестовые данные:
```bash
python manage.py create_test_data
```

7. Запустите сервер:
```bash
python manage.py runserver 8080
```

API будет доступно по адресу: http://localhost:8080/api/

## Развертывание с Docker

### Требования

- Docker
- Docker Compose

### Запуск

1. Перейдите в папку `foodgram/`:
```bash
cd foodgram
```

2. Создайте файл `.env`:
```
SECRET_KEY=your-secret-key-here
DEBUG=False
USE_SQLITE=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your-strong-password
DB_HOST=db
DB_PORT=5432
```

3. Запустите контейнеры:
```bash
docker-compose up -d
```

4. Выполните миграции:
```bash
docker-compose exec backend python manage.py migrate
```

5. Загрузите ингредиенты:
```bash
docker-compose exec backend python manage.py load_ingredients
```

6. Загрузите тестовые данные:
```bash
docker-compose exec backend python manage.py create_test_data
```

7. Создайте суперпользователя:
```bash
docker-compose exec backend python manage.py createsuperuser
```

8. Соберите статические файлы:
```bash
docker-compose exec backend python manage.py collectstatic --noinput
```

Приложение будет доступно по адресу: http://localhost:8080/

## Развертывание на удаленном сервере (Linux)

1. Создайте директорию foodgram:

```bash
mkdir foodgram
```

2. Перейдите в папку с проектом:

```bash
cd foodgram
```

3. Создайте файл .env и заполните его своими данными:

```bash
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
DB_HOST=db
ALLOWED_HOSTS=123.456.789.0
SECRET_KEY=super_secret_key
```

4. Установите Docker Compose:

```bash
sudo apt-get install docker-compose-plugin
```

5. Скопируйте файл docker-compose.production.yml в директорию проекта и поочередно выполните команды:

```bash
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

### Основные эндпоинты:

- `GET /api/users/` - список пользователей
- `POST /api/users/` - регистрация пользователя
- `GET /api/recipes/` - список рецептов
- `POST /api/recipes/` - создание рецепта
- `GET /api/tags/` - список тегов
- `GET /api/ingredients/` - список ингредиентов
- `POST /api/auth/token/login/` - получение токена
- `POST /api/auth/token/logout/` - удаление токена

### Аутентификация

Для доступа к защищенным эндпоинтам используйте токен в заголовке:
```
Authorization: Token <your-token>
```

## Структура проекта

```
foodgram/
├── backend/          # Django backend
│   ├── api/          # API приложение
│   ├── data/         # Данные для загрузки
│   ├── recipes/      # Модели рецептов
│   ├── users/        # Модели пользователей
│   └── foodgram/     # Настройки проекта
├── frontend/         # React frontend
├── infra/            # Nginx конфигурация   
├── docs/             # API документация
├── .github/          # GitHub Actions
├── .env              # Переменные окружения
├── docker-compose.yml # Конфигурация Docker
└── docker-compose.production.yml # Конфигурация Docker для production
```

## Автор

* Семен Репинин https://github.com/SemRepin
