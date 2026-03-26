# Tournament_2026 rewritten to Django

This is a Django + Django REST Framework rewrite of the uploaded FastAPI project.

## What is included

- custom email-based user model
- JWT auth implemented with PyJWT
- tournaments, teams, rounds, submissions, evaluations
- image upload handling for user, team, and tournament images
- admin site registration
- management commands:
  - `python manage.py create_admin`
  - `python manage.py seed_data`
- API routes aligned with the original project under `/api/...`

## Important note

The original archive referenced `Round`, `Submission`, and `Evaluation` in CRUD logic, but those SQLAlchemy models were missing from `app/models.py`.
In this Django rewrite, those models were inferred and implemented from the existing FastAPI CRUD and schema usage.

## Setup

```bash
pip install -r requirements.txt
py manage.py makemigrations tournaments
py manage.py migrate
py manage.py create_admin
py manage.py setup_admin
py manage.py runserver
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


## HTML and API routes
- HTML pages are mounted at `/`
- API endpoints are mounted at `/api/`
- Login page: `/login/`
- Registration page: `/register/`
