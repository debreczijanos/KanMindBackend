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

## Board endpoints

- `GET /api/boards/` – list boards where the authenticated user is the owner or a member. Each item exposes `id`, `title`, `owner_id`, and the task/member counters that the dashboard expects.
- `POST /api/boards/` – create a board. Payload:

```json
{
  "title": "My New Board",
  "description": "Optional text",
  "members": [2, 3]
}
```

The authenticated user automatically becomes the owner and is added as a member. The response returns the full board detail (members list, timestamps, etc.).

- `GET /api/boards/<id>` – board detail used by the board and settings screens. For now `tasks` is an empty list until task management is implemented.
- `PATCH /api/boards/<id>/` – owners can rename the board or update the member list. Always send the full member list when changing members.
- `DELETE /api/boards/<id>/` – owners only.
- `GET /api/email-check/?email=<address>` – validate that another user exists before inviting them to a board. Returns `{ "id", "email", "fullname" }` on success or `404` if the email is unknown.

## CORS

Local frontend servers such as VS Code Live Server (port 5500) are already allowed through `CORS_ALLOWED_ORIGINS` in `settings.py`. Add more origins there if you serve the frontend from another port/domain.
