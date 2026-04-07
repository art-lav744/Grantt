#Grantt

## Setup

```bash
pip install -r requirements.txt
py manage.py makemigrations tournaments
py manage.py migrate
py manage.py create_admin
py manage.py setup_admin
py manage.py seed_data
py manage.py runserver
```

## Test
```bash
py manage.py test
```

## Admin panel
```
http://localhost:8000/admin/
  admin@example.com
  Admin123!
```

## Main endpoints

- `POST /api/register`
- `POST /api/login`
- `POST /api/users/<user_id>/image`
- `GET /api/users/me/team`
- `GET /api/users/me/evaluations`
- `POST /api/tournaments/`
- `GET /api/tournaments/`
- `PATCH /api/tournaments/<id>/status`
- `POST /api/tournaments/<id>/image`
- `GET /api/tournaments/<id>/leaderboard`
- `POST /api/teams/`
- `POST /api/teams/<id>/image`
- `GET /api/members/<email>/tournaments`
- `POST /api/rounds/`
- `POST /api/rounds/<id>/distribute`
- `POST /api/submissions/`

## Authentication

Send the token as:

```http
Authorization: Bearer <token>
```
## Roles

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

## HTML and API routes
- HTML pages are mounted at `/`
- API endpoints are mounted at `/api/`
- Login page: `/login/`
- Registration page: `/register/`

## Picture uploading

```
POST /api/users/me/profile-image/       → media/profile_images/
POST /api/teams/{id}/image/             → media/team_images/
POST /api/tournaments/{id}/image/       → media/tournament_images/
```

Формати: JPEG, PNG, GIF, WEBP. Максимум 5 MB. Фото профілю та команди автоматично кадруються до квадрату 400×400.
