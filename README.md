# Task API

Small FastAPI task manager with in-memory storage.

# Running the project

## Setup (once)
Requires Python 3.10+. From the `task_api` folder (Windows PowerShell):
```
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
On macOS/Linux use `python3 -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.txt`.

## Run the service
```
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
- API: http://127.0.0.1:8000
- Interactive docs (try the endpoints in the browser): http://127.0.0.1:8000/docs
- `--reload` restarts the server when you edit code. Use `--port 8001` if port 8000 is taken.
- Data is held in memory and is lost whenever the service stops.

## Stop the service
- **Foreground:** press `Ctrl+C` in the terminal where it is running.
- **Background / lost terminal (PowerShell):**
  ```
  Get-NetTCPConnection -LocalPort 8000 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
  ```
  (macOS/Linux: `kill $(lsof -ti :8000)`)

## Run the tests
```
.\.venv\Scripts\python.exe -m pytest
```

---

# Main tasks (1-4)

## What was built
- **Task 1 - Data model:** `Task` with UUID `id`, required `title`, optional `description`, `completed` (default `false`) and UTC `created_at`.
- **Task 2 - CRUD:** `POST /tasks` (201), `GET /tasks` (`?completed=` filter), `GET /tasks/{id}` (404 if missing), `PATCH /tasks/{id}` (partial update), `DELETE /tasks/{id}` (204).
- **Task 3 - Errors and validation:** every error returns `{"detail": "..."}`; blank titles are rejected on create and update; unknown routes get a custom 404.
- **Task 4 - Tests:** `tests/test_tasks.py` covers create, 404, PATCH-to-complete, validation, delete, unknown routes and the filter.

## Files
- `app/models.py` - Task and request models (title validation)
- `app/routers/tasks.py` - CRUD endpoints
- `app/errors.py` - exception handlers producing the `{"detail": "..."}` shape
- `app/main.py` - app setup

## Decisions
- `PATCH` applies only the fields sent; explicit `null` for `title`/`completed` is rejected, `description: null` clears it.
- Validation failures return 422, unknown ids 404, malformed UUID 422.
- Deleting a missing task returns 404 (not an idempotent 204).
- Storage is not thread-safe; fine for a single-worker demo.

---

# Bonus challenges

## A - Dependency injection
- `app/storage.py` defines a `TaskRepository` protocol plus an `InMemoryTaskRepository`.
- `app/dependencies.py` provides `get_repository`; route handlers receive the repository through `Depends`.
- To use a real database, implement `TaskRepository` and return it from `get_repository`. Tests override the dependency to get fresh storage per test.

## B - Pagination
- `GET /tasks?limit=&offset=` returns an envelope: `total`, `limit`, `offset`, `next_offset`, `previous_offset`, `items`.
- `limit` defaults to 20 (min 1, max 100); `offset` defaults to 0. It combines with `?completed=`.
- Note: this means `GET /tasks` returns an object, not a bare list.

## C - Background job
- `app/audit.py` appends a timestamped line to `task_audit.log` on every task create and delete, using FastAPI `BackgroundTasks` (runs after the response is sent).
- The log lands in the folder the server is started from; override the path with the `TASK_AUDIT_LOG` environment variable.
