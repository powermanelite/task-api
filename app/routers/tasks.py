from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status

from ..audit import write_audit_entry
from ..dependencies import get_repository
from ..models import Task, TaskCreate, TaskPage, TaskUpdate
from ..storage import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])

Repo = Annotated[TaskRepository, Depends(get_repository)]


def _not_found(task_id: UUID) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"Task {task_id} not found")


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, repo: Repo, background: BackgroundTasks, response: Response):
    task = repo.add(Task(**payload.model_dump()))
    response.headers["Location"] = f"/tasks/{task.id}"
    background.add_task(write_audit_entry, "created", task.id)
    return task


@router.get("", response_model=TaskPage)
def list_tasks(
    repo: Repo,
    completed: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    tasks = repo.list(completed=completed)
    total = len(tasks)
    return TaskPage(
        total=total,
        limit=limit,
        offset=offset,
        next_offset=offset + limit if offset + limit < total else None,
        previous_offset=max(offset - limit, 0) if offset > 0 else None,
        items=tasks[offset : offset + limit],
    )


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: UUID, repo: Repo):
    task = repo.get(task_id)
    if task is None:
        raise _not_found(task_id)
    return task


@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: UUID, payload: TaskUpdate, repo: Repo):
    task = repo.update(task_id, payload.model_dump(exclude_unset=True))
    if task is None:
        raise _not_found(task_id)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, repo: Repo, background: BackgroundTasks):
    if not repo.delete(task_id):
        raise _not_found(task_id)
    background.add_task(write_audit_entry, "deleted", task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
