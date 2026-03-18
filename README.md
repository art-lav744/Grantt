# Tournament_2026 — Django 

## Структура проєкту

```
Tournament_2026/
├── config/                     ← Конфігурація Django-проєкту
│   ├── settings.py             ← Налаштування (БД, JWT, CORS, медіа)
│   ├── urls.py                 ← Головний роутер (HTML + API)
│   ├── wsgi.py
│   └── asgi.py
│
├── tournaments/                ← Основний додаток
│   ├── models.py               ← Моделі БД (User, Tournament, Team, Round, …)
│   ├── serializers.py          ← DRF-серіалізатори
│   ├── views.py                ← HTML-в'юхи та API-в'юхи (APIView)
│   ├── forms.py                ← Django-форми (реєстрація, подача роботи)
│   ├── permissions.py          ← Кастомні DRF-пермішени (JWT-ролі)
│   ├── authentication.py       ← JWT-аутентифікація для DRF
│   ├── utils.py                ← JWT, обробка зображень, валідація пароля
│   ├── admin.py                ← Реєстрація моделей у Django Admin
│   ├── urls.py                 ← HTML-роути
│   └── api_urls.py             ← API-роути (/api/…)
│
├── templates/                  ← HTML-шаблони
│   ├── base.html               ← Базовий шаблон (навігація, стилі)
│   ├── home.html               ← Головна сторінка
│   └── tournaments/
│       ├── tournament_list.html
│       ├── tournament_detail.html
│       ├── team_detail.html
│       ├── dashboard.html
│       └── submission_form.html
│
├── media/                      ← Завантажені зображення (створюється при старті)
│   ├── profile_images/
│   ├── team_images/
│   └── tournament_images/
│
├── requirements.txt            ← Залежності Python
└── db.sqlite3                  ← SQLite база даних
```

## Запуск проєкту

### 1. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 2. Міграції та початкові дані

```bash
python manage.py makemigrations tournaments
python manage.py migrate
python manage.py create_admin
python manage.py seed_data
```

### 3. Запуск сервера

```bash
python manage.py runserver
```

### 4. Перегляд адмін-панелі

```
http://localhost:8000/admin/
  admin@example.com
  Admin123!
```

## Ролі користувачів

| Дія | `admin` | `organizer` | `jury` | `team` |
|-----|---------|-------------|--------|--------|
| Створити турнір | ✅ | ✅ | ❌ | ❌ |
| Змінити статус турніру | ✅ | ✅ | ❌ | ❌ |
| Завантажити обкладинку турніру | ✅ | ✅ | ❌ | ❌ |
| Створити раунд | ✅ | ✅ | ❌ | ❌ |
| Розподілити роботи між журі | ✅ | ✅ | ❌ | ❌ |
| Зареєструвати команду | ❌ | ❌ | ❌ | ✅ |
| Подати роботу | ❌ | ❌ | ❌ | ✅ |
| Переглянути свої оцінки | ❌ | ❌ | ✅ | ❌ |
| Переглянути лідерборд | ✅ | ✅ | ✅ | ✅ |

## Типовий сценарій

### Admin / Organizer
1. Увійти як `admin@example.com`
2. **Tournaments → POST /api/tournaments/**: задати назву, дати реєстрації
3. **PATCH /api/tournaments/{id}/status/**: змінити статус на `registration`
4. **POST /api/rounds/**: створити раунд із дедлайном
5. Після дедлайну: **POST /api/rounds/{id}/distribute/** → автоматичний розподіл між журі
6. **GET /api/tournaments/{id}/leaderboard/**: переглянути результати

### Team
1. Відкрити `/register/` → зареєструватись з роллю `team`
2. Увійти → перейти до `/tournaments/`
3. Знайти турнір зі статусом `registration` → зареєструвати команду через API
4. Коли турнір активний: **POST /api/submissions/** → вставити GitHub-посилання

### Jury
1. Зареєструватись або бути доданим адміністратором з роллю `jury`
2. Після розподілу: **GET /api/users/me/evaluations/** → переглянути призначені роботи

## API Endpoints

# ── Auth ─────────────────────────────────────────────────────────────────────
POST   /api/auth/register/                  — Реєстрація акаунту         [public]  +
POST   /api/auth/login/                     — Вхід, отримання JWT        [public]  +

# ── Users ────────────────────────────────────────────────────────────────────
POST   /api/users/me/profile-image/         — Завантажити фото профілю   [auth]  +
GET    /api/users/me/teams/                 — Мої команди                [auth]  +
GET    /api/users/me/evaluations/           — Мої оцінки                 [jury]  +

# ── Tournaments ───────────────────────────────────────────────────────────────
GET    /api/tournaments/                    — Список турнірів             [public]  +
POST   /api/tournaments/                    — Створити турнір             [admin/organizer]  +
PATCH  /api/tournaments/{id}/status/        — Змінити статус              [admin/organizer]  +
GET    /api/tournaments/{id}/leaderboard/   — Таблиця лідерів            [public]  +

# ── Teams ─────────────────────────────────────────────────────────────────────
POST   /api/teams/                          — Зареєструвати команду       [auth]  +
GET    /api/members/{email}/tournaments/    — Турніри учасника            [auth]  +

# ── Rounds ────────────────────────────────────────────────────────────────────
POST   /api/rounds/                         — Створити раунд              [admin/organizer]  +
PATCH  /api/rounds/{id}/status/             — Змінити статус раунду       [admin/organizer]  -
POST   /api/rounds/{id}/distribute/         — Розподілити по журі         [admin/organizer]  +

# ── Submissions ───────────────────────────────────────────────────────────────
POST   /api/submissions/                    — Подати роботу               [auth]  +
GET    /api/rounds/{id}/submissions/        — Список сабмітів             [admin/organizer]  -

# ── Evaluations ───────────────────────────────────────────────────────────────
GET    /api/evaluations/my/                 — Мої оцінки                  [jury]  -
PUT    /api/evaluations/{id}/               — Виставити оцінку            [jury]  -

# ── Images ────────────────────────────────────────────────────────────────────
POST   /api/users/me/profile-image/         — Фото профілю користувача   [auth]  +
POST   /api/teams/{id}/image/               — Фото команди                [auth]  +
POST   /api/tournaments/{id}/image/         — Обкладинка турніру          [admin/organizer]  +

## Формула підрахунку балів

```
tech_avg = середнє tech_score від усіх оцінок журі
func_avg = середнє func_score від усіх оцінок журі
total    = (tech_avg + func_avg) / 2
```

Всі оцінки від 0 до 100.

## Завантаження зображень

```
POST /api/users/me/profile-image/       → media/profile_images/
POST /api/teams/{id}/image/             → media/team_images/
POST /api/tournaments/{id}/image/       → media/tournament_images/
```

Формати: JPEG, PNG, GIF, WEBP. Максимум 5 MB. Фото профілю та команди автоматично кадруються до квадрату 400×400.

## Аутентифікація

JWT-токен діє **24 години**. Передавати у заголовку:

```http
Authorization: Bearer <token>
```

## Змінні середовища

| Змінна | За замовчуванням | Опис |
|--------|-----------------|------|
| `DJANGO_SECRET_KEY` | `change-me-in-production` | Секретний ключ Django |
| `DJANGO_DEBUG` | `1` | Режим дебагу (`0` для продакшну) |
| `DJANGO_ALLOWED_HOSTS` | `*` | Дозволені хости (через кому) |
| `JWT_SECRET_KEY` | = `SECRET_KEY` | Ключ підпису JWT |