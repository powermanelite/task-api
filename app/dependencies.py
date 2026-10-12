from .storage import InMemoryTaskRepository, TaskRepository

_repository = InMemoryTaskRepository()


def get_repository() -> TaskRepository:
    return _repository
