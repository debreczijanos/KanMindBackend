# KanMind Backend

Python/Django backend that powers the Kanban board frontend. It exposes a REST API for authentication and will be extended with board/task management endpoints.

## Quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/`.

## Registration endpoint

`POST /api/auth/register/`

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "Sup3rSecret!",
  "first_name": "Alice",
  "last_name": "Doe"
}
```

Successful requests return the created user plus an auth token:

```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Doe"
  },
  "token": "0123456789abcdef..."
}
```

The token can be provided in subsequent requests using an `Authorization: Token <token>` header. All future Kanban board/task endpoints will require an authenticated user.
