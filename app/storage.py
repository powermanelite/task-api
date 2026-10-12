from typing import Protocol
from uuid import UUID

from .models import Task


class TaskRepository(Protocol):
    """Storage contract. Implement this for a real database and swap it in
    via the `get_repository` dependency."""

    def add(self, task: Task) -> Task: ...
    def get(self, task_id: UUID) -> Task | None: ...
    def list(self, completed: bool | None = None) -> list[Task]: ...
    def update(self, task_id: UUID, changes: dict) -> Task | None: ...
    def delete(self, task_id: UUID) -> bool: ...


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}

    def add(self, task: Task) -> Task:
        self._tasks[task.id] = task
        return task

    def get(self, task_id: UUID) -> Task | None:
        return self._tasks.get(task_id)

    def list(self, completed: bool | None = None) -> list[Task]:
        tasks = sorted(self._tasks.values(), key=lambda t: t.created_at)
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def update(self, task_id: UUID, changes: dict) -> Task | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        updated = task.model_copy(update=changes)
        self._tasks[task_id] = updated
        return updated

    def delete(self, task_id: UUID) -> bool:
        return self._tasks.pop(task_id, None) is not None
