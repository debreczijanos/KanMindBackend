# KanMind Backend

Lightweight Django REST API für Authentifizierung, Boards, Tasks und Kommentare – gebaut für das KanMind-Frontend.

## Overview
- Token-basierte Auth (Registration + Login).
- Board-Management mit Member-Verwaltung (Owner-gated Updates/Deletes).
- Tasks inkl. Assignee/Reviewer, Status, Priorität, Due Date und Kommentar-Thread.
- Fertige JSON-Responses, die das Frontend erwartet (Counters, comments_count).

## Tech Stack
- Python 3.12, Django 5, Django REST Framework, TokenAuth
- SQLite (dev), CORS Middleware

## Project Structure
```
core/               # settings.py, urls.py, wsgi.py, asgi.py
auth_app/           # Auth endpoints (login, registration, email-check)
boards_app/         # Boards + permissions + serializers
tasks_app/          # Tasks, comments, permissions
manage.py
requirements.txt
```

## Installation
Prerequisites: Python 3.12+

**Mac/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional
python manage.py runserver
```

**Windows (PowerShell)**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional
python manage.py runserver
```

API-Base: `http://127.0.0.1:8000/api/`

## API Endpoints (kurz)

### Auth (`/api/`)
- `POST /registration/`
  ```json
  {"fullname":"Alice Doe","email":"alice@example.com","password":"Sup3rSecret!","repeated_password":"Sup3rSecret!"}
  ```
  Response: `token`, `user_id`, `email`, `fullname`

- `POST /login/`
  ```json
  {"email":"alice@example.com","password":"Sup3rSecret!"}
  ```
  Response: wie Registration

- `GET /email-check/?email=user@example.com` (Token nötig)
  - 404 wenn Nutzer nicht existiert, sonst `{id,email,fullname}`

### Boards (`/api/boards/`) – Token nötig
- `GET /` – Boards des Users (owner oder member) inkl. Counters.
- `POST /`
  ```json
  {"title":"My Board","description":"Optional","members":[2,3]}
  ```
- `GET /<id>/` – Board + Members + Tasks (inkl. assignee/reviewer + comments_count).
- `PATCH /<id>/` – nur Owner. Vollständige Memberliste senden wenn geändert.
- `DELETE /<id>/` – nur Owner.

### Tasks (`/api/tasks/`) – Token nötig
- `POST /`
  ```json
  {"board":1,"title":"Demo","description":"","status":"to-do","priority":"medium","assignee_id":null,"reviewer_id":null,"due_date":"2025-11-30"}
  ```
  Hinweis: assignee/reviewer müssen Board-Member sein (oder null).

- `PATCH /<id>/` – Felder nach Bedarf; Board kann nicht gewechselt werden.
- `DELETE /<id>/`
- `GET /assigned-to-me/` – Tasks, bei denen der User Assignee ist.
- `GET /reviewing/` – Tasks, bei denen der User Reviewer ist.

### Task Comments (`/api/tasks/<task_id>/comments/`) – Token nötig
- `GET /` – Liste der Comments.
- `POST /`
  ```json
  {"content":"Nice update"}
  ```
- `DELETE /<comment_id>/` – Autor oder Board-Owner.

## Authentifizierung
Alle geschützten Endpoints erwarten `Authorization: Token <token>`.

## CORS
Erlaubte Origins (dev): `http://127.0.0.1:5500`, `http://localhost:5500`, `http://127.0.0.1:5173`, `http://localhost:5173`. Bei Bedarf `CORS_ALLOWED_ORIGINS` in `core/settings.py` erweitern.
