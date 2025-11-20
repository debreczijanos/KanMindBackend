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

- `GET /api/boards/<id>` – board detail used by the board and settings screens (includes members and the board’s tasks with assignee/reviewer info).
- `PATCH /api/boards/<id>/` – owners can rename the board or update the member list. Always send the full member list when changing members.
- `DELETE /api/boards/<id>/` – owners only.
- `GET /api/email-check/?email=<address>` – validate that another user exists before inviting them to a board. Returns `{ "id", "email", "fullname" }` on success or `404` if the email is unknown.

## Task endpoints

- `POST /api/tasks/` – create a task. Payload mirrors the frontend form:

```json
{
  "board": 1,
  "title": "Wireframe UI",
  "description": "Collect feedback",
  "status": "to-do",
  "priority": "medium",
  "due_date": "2025-11-30",
  "assignee_id": 2,
  "reviewer_id": 3
}
```

`assignee_id` / `reviewer_id` are optional and must reference board members.

- `PATCH /api/tasks/<id>/` – update a task (status moves, edits, etc.). Send the fields you want to change; the board cannot be changed.
- `DELETE /api/tasks/<id>/` – delete a task.
- `GET /api/boards/<id>/` already returns the board with its tasks, including nested assignee/reviewer info that the board page renders.
- `GET /api/tasks/assigned-to-me/` – dashboard list of tasks where the current user is the assignee. Includes `comments_count`, `board`, and `due_date`.
- `GET /api/tasks/reviewing/` – tasks where the current user is the reviewer.

### Task comments

- `GET /api/tasks/<task_id>/comments/` – list comments for a task.
- `POST /api/tasks/<task_id>/comments/` – add a comment with `{ "content": "Nice update" }`. Author + timestamp are filled automatically.
- `DELETE /api/tasks/<task_id>/comments/<comment_id>/` – comment author or the board owner can delete comments.

## CORS

Local frontend servers such as VS Code Live Server (port 5500) are already allowed through `CORS_ALLOWED_ORIGINS` in `settings.py`. Add more origins there if you serve the frontend from another port/domain.
