import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_repository
from app.main import app
from app.storage import InMemoryTaskRepository


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TASK_AUDIT_LOG", str(tmp_path / "audit.log"))
    repo = InMemoryTaskRepository()  # fresh storage per test
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
