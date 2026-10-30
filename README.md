# Freelance CRM API

REST API для учёта клиентов, заказов, этапов и оплат фрилансера. Изоляция данных по владельцу, JWT-аутентификация, аналитика на ORM-агрегациях, OpenAPI-документация, Docker Compose для запуска одной командой.

## Стек

Python 3.12 · Django 6.1 · Django REST Framework · SimpleJWT · django-filter · drf-spectacular (Swagger) · PostgreSQL 16 · Redis · Docker / Docker Compose · pytest + pytest-django · gunicorn

## Возможности

- **CRUD клиентов, заказов, этапов, оплат** — `/api/clients/`, `/api/orders/`, `/api/milestones/`, `/api/payments/` (пагинация, фильтр, поиск, сортировка)
- **JWT-авторизация** — `/api/token/`, `/api/token/refresh/`, все endpoints за `IsAuthenticated`
- **Изоляция данных по владельцу** — `get_queryset` + `perform_create` по `request.user`, queryset в сериализаторах режется по владельцу, для вложенных сущностей — фильтр через связь `order__owner`
- **Валидация на уровне сериализаторов** — положительный бюджет, запрет дедлайна в прошлом, невозможность привязать заказ/оплату к чужим данным
- **Аналитика на ORM:**
  - `GET /api/analytics/revenue-by-month/` — выручка по месяцам (`TruncMonth + Sum`)
  - `GET /api/analytics/overdue/` — просроченные заказы, 1 SQL-запрос
  - `GET /api/analytics/payments/` — бюджет / оплачено / долг (`Coalesce + Sum`)
- **Swagger** — `/api/schema/swagger-ui/`
- **Админка Django** — клиенты, заказы, этапы, оплаты

## Оптимизация N+1: 4 запроса → 1

Endpoint `overdue` отдаёт заказ + имя клиента. Без оптимизации это классический N+1: 1 запрос за заказы + по запросу за каждым клиентом, на 3 заказах — 4 запроса.

Решение — `select_related("client")`:

```python
orders = Order.objects.filter(
    Q(deadline__lt=timezone.now()), ~Q(status="done"), owner=request.user
).select_related("client")
```

Плюс стабильный `Meta.ordering` на всех моделях, чтобы пагинация не давала плавающий порядок строк.

Проверка зафиксирована тестом — упадёт при возврате N+1:

```python
with django_assert_num_queries(1):
    response = api_client.get("/api/analytics/overdue/")
```

## Быстрый старт

### Docker

```bash
cp .env.example .env
docker compose up --build
docker compose exec web python manage.py createsuperuser
```

API: http://localhost:8000/api/ · Swagger: http://localhost:8000/api/schema/swagger-ui/

### Локально

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up db -d
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Конфигурация — через `.env` (см. `.env.example`): `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `POSTGRES_*`, `REDIS_URL`.

Прод-режим в контейнере: `gunicorn config.wsgi:application --bind 0.0.0.0:8000`.

## Endpoints

| Метод                          | Путь                                        | Доступ   |
| ------------------------------ | ------------------------------------------- | -------- |
| POST                           | `/api/token/`, `/api/token/refresh/`        | открытый |
| GET/POST, GET/PUT/PATCH/DELETE | `/api/clients/`, `/api/clients/{id}/`       | свой     |
| GET/POST, GET/PUT/PATCH/DELETE | `/api/orders/`, `/api/orders/{id}/`         | свой     |
| GET/POST, GET/PUT/PATCH/DELETE | `/api/milestones/`, `/api/milestones/{id}/` | свой     |
| GET/POST, GET/PUT/PATCH/DELETE | `/api/payments/`, `/api/payments/{id}/`     | свой     |
| GET                            | `/api/analytics/revenue-by-month/`          | свой     |
| GET                            | `/api/analytics/overdue/`                   | свой     |
| GET                            | `/api/analytics/payments/`                  | свой     |
| GET                            | `/api/schema/swagger-ui/`                   | открытый |

Фильтры: `?company=`, `?client=`, `?order=`. Поиск: `?search=`. Сортировка: `?ordering=`.

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo12345"}'

curl http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer <access>"
```

## Структура

```
config/               # settings, urls, wsgi/asgi
crm/
  models.py           # Client, Order, Milestone, Payment
  serializers.py      # валидация budget/deadline, срез queryset по владельцу
  views.py            # ViewSet'ы + AnalyticsViewSet на агрегациях
  urls.py             # DefaultRouter
  admin.py
  tests/              # pytest-тесты
  migrations/
Dockerfile            # python:3.12-slim + gunicorn
docker-compose.yaml   # db + redis + web
```

## Тесты

```bash
pytest -q
```

Покрыто: изоляция чужих заказов, запрет создания заказа на чужого клиента, overdue — ровно 1 запрос. Запуск на Postgres из `.env`.

## Заметки

- `Redis` поднят в compose как сервис для кэша/троттлинга, приложение пока работает без него.
- Дальше: `SPECTACULAR_SETTINGS`, троттлинг JWT-endpoints, `requirements-dev.txt`, GitHub Actions (`pytest + ruff`).
