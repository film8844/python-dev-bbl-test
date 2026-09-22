# Python Developer Assessment BBL

Appointment booking app — FastAPI + SQLite + static HTML/Tailwind.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)

## Run

```bash
uv sync
uv run fastapi dev src/app.py
```

Open http://127.0.0.1:8000 — the login page loads and the database is created and seeded on first start.

## Demo accounts

| Username | Password | Role |
|---|---|---|
| `admin` | `admin1234` | admin |
| `user1` | `user1234` | user |
| `user2` | `user2234` | user |

## Test

```bash
uv run pytest
```

## API

Swagger UI: http://127.0.0.1:8000/docs (click **Authorize** and paste the `access_token` from login)

| Method | Path | Access |
|---|---|---|
| `POST` | `/api/auth/login` | public |
| `POST` | `/api/auth/register` | public |
| `GET` | `/api/auth/me` | any user |
| `GET` | `/api/booking/slots` | any user |
| `POST` | `/api/booking/` | any user, books for themselves |
| `GET` | `/api/booking/` | admin sees all, others see only their own |
| `GET` | `/api/booking/all` | admin only |
| `GET` `PATCH` `DELETE` | `/api/booking/{id}` | owner or admin |

## Notes

- Auth is a stateless JWT (`Authorization: Bearer <token>`), 1 hour expiry. `/api/auth/logout` only tells the client to drop the token.
- A time slot can hold one active booking, enforced by a partial unique index in SQLite. Cancelling is a soft delete, so the slot becomes available again.
- `database.db` is created relative to the working directory, so run the commands above from the project root.
- The dev `jwt_secret` in `src/core/config.py` is for local use only — override it with an env var or `.env` in production.
