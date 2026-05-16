# Grantt Tournament Platform

Grantt is a tournament management app with a Django REST backend and an Angular frontend.

The backend handles users, roles, tournaments, teams, rounds, submissions, jury assignment, scoring, leaderboards, tournament files, banners, and email verification. The frontend is in `frontend/` and talks to the API at `http://127.0.0.1:8000/api`.

## Requirements

Install these before the first run:

- Python 3.10+; Python 3.11 or newer is recommended.
- Node.js 20.19+ or 22+.
- npm 10+; the project was tested with npm 11.
- Git.
- SQLite is used by default, so no external database is required.

Check versions:

```powershell
py --version
node --version
npm --version
git --version
```

## Project Structure

```text
.
├── config/                 Django project settings and URLs
├── tournaments/            Django app, API, models, tests, seed command
├── frontend/               Angular app
├── media/                  Uploaded local files, generated at runtime
├── db.sqlite3              Local SQLite database, generated after migrations
├── manage.py
├── requirements.txt
└── README.md
```

## Environment

Create `.env` in the project root if you need custom settings:

```env
DJANGO_SECRET_KEY=dev-secret-key
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
JWT_SECRET_KEY=dev-jwt-secret

# Local development default is console email backend.
# Registration emails will be printed in the backend terminal.
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Use these only if you want real SMTP email.
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST_USER=your_email@gmail.com
# EMAIL_HOST_PASSWORD=your_gmail_app_password
```

Without `.env`, the app still runs locally. Email verification links are printed to the Django terminal because the default backend is `console.EmailBackend`.

## First Backend Run

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
py manage.py makemigrations
py manage.py migrate
py manage.py seed_data
py manage.py runserver
```

Backend URLs:

- API: `http://127.0.0.1:8000/api/`
- Django admin: `http://127.0.0.1:8000/admin/`
- Media files in development: `http://127.0.0.1:8000/media/...`

If PowerShell blocks venv activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## First Frontend Run

Open a second terminal:

```powershell
cd frontend
npm install
npm start
```

Frontend URL:

```text
http://localhost:4200
```

Keep the backend running at `http://127.0.0.1:8000`, because `frontend/src/app/services/api.ts` uses that API URL.

## Demo Data

Run this any time to recreate the demo tournaments:

```powershell
py manage.py seed_data
```

The command deletes only the demo tournaments named:

- `Grantt Championship 2026 #1`
- `Grantt Championship 2026 #2`
- `Grantt Championship 2026 #3`

It updates or creates demo users and marks them as verified.

All seeded accounts use this password:

```text
Admin123!
```

Demo accounts:

| Role | Email |
| --- | --- |
| Admin | `admin@example.com` |
| Organizer | `organizer@techcup.ua` |
| Jury | `jury1@gmail.com` |
| Jury | `jury2@gmail.com` |
| Jury | `jury3@gmail.com` |
| Participant | `participant1@gmail.com` |
| Participant | `participant2@gmail.com` |
| Participant | `participant3@gmail.com` |
| Participant | `participant4@gmail.com` |
| Participant | `participant5@gmail.com` |
| Participant | `participant6@gmail.com` |
| Participant | `participant7@gmail.com` |
| Participant | `participant8@gmail.com` |
| Participant | `participant9@gmail.com` |
| Participant | `participant10@gmail.com` |
| Participant | `participant11@gmail.com` |
| Participant | `participant12@gmail.com` |

Seeded tournament coverage:

- Tournament #1: registration is open, teams exist, first round is planned.
- Tournament #2: tournament is active, round is active, submissions and partial evaluations exist.
- Tournament #3: tournament is closed, two rounds are completed, leaderboard has evaluated results.
- Every tournament has demo files.
- Jury users are approved and assigned to every seeded tournament.

## Common Commands

Backend:

```powershell
py manage.py runserver
py manage.py migrate
py manage.py makemigrations
py manage.py seed_data
py manage.py check
py manage.py test
```

Frontend:

```powershell
cd frontend
npm start
npm run build
npm test
```

## Tests

Run all backend tests:

```powershell
py manage.py test
```

Run one test module:

```powershell
py manage.py test tournaments.tests.test_tournament_files_access
```

Run frontend build validation:

```powershell
cd frontend
npm run build
```

Known current build warnings:

- Initial Angular bundle is above the configured warning budget.
- Some component SCSS files are above the configured warning budget.

These are warnings, not build failures.

## API Authentication

Login returns JWT tokens. Authenticated API requests use:

```http
Authorization: Bearer <access_token>
```

Important endpoints:

```text
POST   /api/auth/register/
POST   /api/auth/login/
GET    /api/users/me/
PATCH  /api/users/me/
GET    /api/users/me/teams/
GET    /api/users/me/evaluations/

GET    /api/tournaments/
POST   /api/tournaments/
GET    /api/tournaments/{id}/
PATCH  /api/tournaments/{id}/
PATCH  /api/tournaments/{id}/status/
POST   /api/tournaments/{id}/image/
GET    /api/tournaments/{id}/leaderboard/
GET    /api/tournaments/{id}/files/
POST   /api/tournaments/{id}/files/

GET    /api/tournaments/{id}/teams/
POST   /api/teams/
GET    /api/teams/{id}/
POST   /api/teams/{id}/members/
DELETE /api/teams/{id}/members/{member_id}/

GET    /api/rounds/?tournament_id={id}
POST   /api/rounds/
GET    /api/rounds/{id}/
PATCH  /api/rounds/{id}/
POST   /api/rounds/{id}/distribute/

POST   /api/submissions/
GET    /api/evaluations/{id}/
PATCH  /api/evaluations/{id}/

POST   /api/jury/registrations/
GET    /api/jury/registrations/pending/
PATCH  /api/jury/registrations/{id}/review/

GET    /api/staff/users/
POST   /api/staff/roles/
DELETE /api/admin/teams/{id}/
```

## Role Rules

| Action | Admin | Organizer | Jury | Participant |
| --- | --- | --- | --- | --- |
| Create tournament | Yes | Yes | No | No |
| Edit tournament | Yes | Yes | No | No |
| Upload tournament banner | Yes | Yes | No | No |
| Upload tournament files | Yes | Yes | No | No |
| View tournament files | Yes | Yes | Assigned/approved only | Registered team only |
| Create rounds | Yes | Yes | No | No |
| Distribute works to jury | Yes | Yes | No | No |
| Assign admin/jury roles | Yes | Yes | No | No |
| Register a team | No | No | No | Yes |
| Add/remove team members | No | No | No | Captain only, while registration is open |
| Submit work | No | No | No | Captain only |
| Evaluate assigned work | No | No | Yes | No |
| View leaderboard | Yes | Yes | Yes | Yes |

## Email Verification

Newly registered users must confirm email before login.

In local development, verification links are printed in the Django terminal after registration. Open the printed `/verify/<uid>/<token>/` link in the browser to verify the account.

For real email sending, configure SMTP in `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
```

## Uploads

Uploaded files are stored under `media/`.

Main upload locations:

```text
media/profile_images/
media/team_images/
media/tournaments/
media/tournament_files/
```

Supported image formats are validated in backend utilities. Tournament files allow common document, archive, and image extensions such as PDF, DOCX, XLSX, PPTX, TXT, ZIP, PNG, JPG, and JPEG.

## Reset Local Data

To reset the local SQLite database:

```powershell
Remove-Item db.sqlite3
py manage.py migrate
py manage.py seed_data
```

This removes all local data. Do it only for local development.

## Troubleshooting

If the frontend shows `403 Forbidden` for tournament files:

- Check that the user is logged in.
- Participants must be in a team registered for that tournament.
- Jury must be assigned or approved for that tournament.
- Admin and organizer should always have access.

If registration works but login fails:

- Confirm the email through the verification link printed in the backend terminal.
- Seeded users are already verified.

If frontend pages load but API data is missing:

- Make sure Django is running on `http://127.0.0.1:8000`.
- Make sure Angular is running on `http://localhost:4200`.
- Check browser devtools Network tab for failed API requests.

If `npm run build` shows budget warnings:

- The build still succeeds unless Angular reports an error.
- Current warnings are about configured bundle/style budget thresholds.
