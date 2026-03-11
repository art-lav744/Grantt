# Grantt — Tournament Platform

Веб-платформа для проведення командних турнірів з програмування.

## Структура проєкту

```
tournament_app/          ← Python пакет (бекенд)
  __init__.py
  database.py            ← SQLAlchemy / SQLite
  models.py              ← Таблиці БД
  schemas.py             ← Pydantic-схеми
  crud.py                ← Бізнес-логіка
  utils.py               ← Хешування, JWT, завантаження файлів
  main.py                ← FastAPI роути

requirements.txt         ← Залежності Python

dashboard_admin.html     ← Адмін-панель (Турніри, Раунди, Журі, Лідерборд)
dashboard_team.html      ← Кабінет команди (Реєстрація, Здача роботи, Таймер)
dashboard_jury.html      ← Кабінет журі (Оцінювання з повзунками)

register.html            ← Публічна форма реєстрації акаунту
register_team.html       ← Публічна форма реєстрації команди
create_tournament.html   ← Форма створення турніру
upload_*.html            ← Форми завантаження зображень
```

## Запуск бекенду

### 1. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
# Якщо запускаєте з батьківської папки:
uvicorn tournament_app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Перегляд API документації

```
http://localhost:8000/docs
```

## Ролі користувачів

| Роль | Опис |
|------|------|
| `admin` | Повний доступ: турніри, раунди, журі, розподіл |
| `organizer` | Управління турнірами та раундами |
| `jury` | Оцінювання призначених робіт |
| `team` | Реєстрація команди, здача робіт |

## Типовий сценарій

### Admin
1. Відкрити `dashboard_admin.html`
2. **Турніри → Новий турнір**: задати назву, дати реєстрації
3. **Турніри → Статус**: змінити на `registration`
4. **Журі**: зареєструвати членів журі
5. **Раунди → Новий раунд**: задати завдання та дедлайн
6. **Раунди → Статус**: змінити на `active`
7. Після дедлайну: **Розподіл журі** → кнопка "Розподілити"
8. **Таблиця лідерів**: переглянути результати

### Team
1. Відкрити `dashboard_team.html`
2. Зареєструватись або увійти
3. **Турніри**: знайти турнір зі статусом `registration`
4. **Моя команда → Зареєструвати команду**
5. Коли турнір `running`: **Здати роботу** → вставити посилання до дедлайну

### Jury
1. Відкрити `dashboard_jury.html`
2. Увійти з роллю `jury`
3. Переглянути призначені роботи
4. Натиснути "Оцінити →" → рухати повзунки → "Зафіналізувати"

## API Endpoints (ключові)

```
POST   /auth/register         — Реєстрація
POST   /auth/login            — Вхід, отримання JWT
GET    /auth/me               — Поточний користувач

GET    /tournaments/          — Список (фільтр: ?status=running)
POST   /tournaments/          — Створити [admin/organizer]
PATCH  /tournaments/{id}/status — Змінити статус
GET    /tournaments/{id}/leaderboard — Таблиця лідерів

POST   /rounds/               — Створити раунд [admin/organizer]
PATCH  /rounds/{id}/status    — Змінити статус раунду
POST   /rounds/{id}/distribute — Розподілити по журі [admin]

POST   /teams/                — Зареєструвати команду
GET    /tournaments/{id}/teams — Команди турніру

POST   /submissions/          — Здати роботу (з оновленням)
GET    /rounds/{id}/submissions — Список сабмітів [admin]

GET    /evaluations/my        — Мої оцінки [jury]
PUT    /evaluations/{id}      — Виставити оцінку [jury]
```

## Формула підрахунку балів

```
tech_avg = (code_quality + database + frontend) / 3
func_avg = (requirements + stability + usability) / 3
total    = (tech_avg + func_avg) / 2
```

Всі категорії оцінюються від 0 до 100.

## Завантаження зображень

```
POST /teams/{id}/image          → /static/team_images/
POST /users/{id}/image          → /static/profile_images/
POST /tournaments/{id}/image    → /static/tournament_images/
```

Формати: JPEG, PNG, GIF, WEBP. Максимум 5 MB.
