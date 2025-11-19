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

## Auth endpoints

### Registration

`POST /api/registration/`

```json
{
  "fullname": "Alice Doe",
  "email": "alice@example.com",
  "password": "Sup3rSecret!",
  "repeated_password": "Sup3rSecret!"
}
```

Successful requests return the created user plus an auth token:

```json
{
  "token": "0123456789abcdef...",
  "user_id": 1,
  "email": "alice@example.com",
  "fullname": "Alice Doe"
}
```

### Login

`POST /api/login/`

```json
{
  "email": "alice@example.com",
  "password": "Sup3rSecret!"
}
```

Response matches the registration payload (token, user_id, email, fullname).

The token can be provided in subsequent requests using an `Authorization: Token <token>` header. All future Kanban board/task endpoints will require an authenticated user.

## CORS

Local frontend servers such as VS Code Live Server (port 5500) are already allowed through `CORS_ALLOWED_ORIGINS` in `settings.py`. Add more origins there if you serve the frontend from another port/domain.
