# Grantt — Tournament Platform

Веб-платформа для проведення командних турнірів з програмування.

## Структура проєкту

```
Tournament_2026/
├── app/                        ← Python пакет (бекенд)
│   ├── __init__.py
│   ├── database.py             ← SQLAlchemy / SQLite
│   ├── models.py               ← Таблиці БД
│   ├── schemas.py              ← Pydantic-схеми
│   ├── crud.py                 ← Бізнес-логіка
│   ├── utils.py                ← Хешування, JWT, обробка зображень
│   └── main.py                 ← FastAPI роути
│
├── frontend/                   ← HTML інтерфейси
│   ├── dashboard_admin.html     ← Адмін-панель (Турніри, Раунди, Журі, Лідерборд)
│   ├── dashboard_team.html      ← Кабінет команди (Реєстрація, Здача роботи, Таймер)
│   ├── dashboard_jury.html      ← Кабінет журі (Оцінювання з повзунками)
│   │
│   ├── register.html            ← Публічна форма реєстрації акаунту
│   ├── register_team.html       ← Публічна форма реєстрації команди
│   ├── create_tournament.html   ← Форма створення турніру
│   └── upload_*.html            ← Форми завантаження зображень
│
├── scripts/                    ← Утилітні скрипти
│   ├── create_admin.py         ← Створення адміністратора
│   └── seed_data.py            ← Тестові дані (турнір)
│
├── uploads/                    ← Завантажені зображення
│   ├── team_images/
│   ├── profile_images/
│   └── tournament_images/
│
├── requirements.txt            ← Залежності Python
└── tournament.db               ← SQLite база даних
```

## Запуск бекенду

### 1. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
# Якщо запускаєте з батьківської папки:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Перегляд API документації

```
http://localhost:8000/docs
```

## Ролі користувачів

| Дія |  `admin` | `organizer` | `jury` | `team` |
|-----|-------|-----------|------|------|
| Створити турнір | ✅ | ❌ | ❌ | ❌ |
| Змінити статус турніру | ✅ | ✅ | ❌ | ❌ |
| Редагувати турнір | ✅ | ✅ | ❌ | ❌ |
| Створити раунд | ✅ | ✅ | ❌ | ❌ |
| Розподілити журі | ✅ | ✅ | ❌ | ❌ |
| Зареєструвати команду | ❌ | ❌ | ❌ | ✅ |
| Подати роботу | ❌ | ❌ | ❌ | ✅ |
| Виставити оцінку | ❌ | ❌ | ✅ | ❌ |
| Переглянути лідерборд | ✅ | ✅ | ✅ | ✅ |
| Переглянути профіль | ✅ | ✅ | ✅ | ✅ |

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

## API Endpoints
```
# ── Auth ─────────────────────────────────────────────────────────
POST   /registet                — Реєстрація          [public] +
POST   /login                 — Вхід, отримання JWT [public] +

# ── Tournaments ──────────────────────────────────────────────────
GET    /tournaments/          — Список турнірів        [public] +
POST   /tournaments/          — Створити турнір        [admin] +
PATCH  /tournaments/{id}/status — Змінити статус       [admin/organizer] +
GET    /tournaments/{id}/leaderboard — Таблиця лідерів [public] +

# ── Rounds ───────────────────────────────────────────────────────
POST   /rounds/               — Створити раунд        [admin/organizer] +
PATCH  /rounds/{id}/status    — Змінити статус раунду [admin/organizer] -
POST   /rounds/{id}/distribute — Розподілити по журі  [admin/organizer] +

# ── Teams ────────────────────────────────────────────────────────
POST   /teams/                — Зареєструвати команду [auth] +
GET    /tournaments/{id}/teams — Команди турніру      [public] -

# ── Submissions ──────────────────────────────────────────────────
POST   /submissions/          — Здати роботу      [auth] +
GET    /rounds/{id}/submissions — Список сабмітів [admin/organizer] -

# ── Evaluations ──────────────────────────────────────────────────
GET    /evaluations/my        — Мої оцінки       [jury] - 
PUT    /evaluations/{id}      — Виставити оцінку [jury] -
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
