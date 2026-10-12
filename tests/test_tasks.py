from uuid import uuid4


def create(client, **body):
    body.setdefault("title", "Write tests")
    return client.post("/tasks", json=body)


def test_create_task(client):
    res = create(client, description="cover the API")
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Write tests"
    assert data["description"] == "cover the API"
    assert data["completed"] is False
    assert data["id"] and data["created_at"]
    assert res.headers["location"] == f"/tasks/{data['id']}"


def test_get_missing_task_returns_404(client):
    res = client.get(f"/tasks/{uuid4()}")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_complete_task_via_patch(client):
    task = create(client).json()
    res = client.patch(f"/tasks/{task['id']}", json={"completed": True})
    assert res.status_code == 200
    body = res.json()
    assert body["completed"] is True
    assert body["title"] == task["title"]  # untouched fields preserved
    assert client.get(f"/tasks/{task['id']}").json()["completed"] is True


def test_blank_title_rejected_on_create_and_update(client):
    res = create(client, title="   ")
    assert res.status_code == 422
    assert "blank" in res.json()["detail"]

    task = create(client).json()
    res = client.patch(f"/tasks/{task['id']}", json={"title": ""})
    assert res.status_code == 422
    assert client.get(f"/tasks/{task['id']}").json()["title"] == "Write tests"


def test_title_longer_than_200_chars_rejected(client):
    assert create(client, title="x" * 200).status_code == 201
    res = create(client, title="x" * 201)
    assert res.status_code == 422
    assert "200" in res.json()["detail"]

    task = create(client).json()
    assert client.patch(f"/tasks/{task['id']}", json={"title": "x" * 201}).status_code == 422


def test_malformed_json_returns_readable_422(client):
    res = client.post("/tasks", content="{bad", headers={"content-type": "application/json"})
    assert res.status_code == 422
    assert res.json() == {"detail": "JSON decode error"}


def test_missing_body_and_field_messages(client):
    assert client.post("/tasks").json() == {"detail": "body: Field required"}
    assert client.post("/tasks", json={}).json() == {"detail": "title: Field required"}


def test_patch_missing_task_returns_404(client):
    assert client.patch(f"/tasks/{uuid4()}", json={"completed": True}).status_code == 404


def test_delete_task(client):
    task = create(client).json()
    assert client.delete(f"/tasks/{task['id']}").status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404
    assert client.delete(f"/tasks/{task['id']}").status_code == 404


def test_invalid_uuid_returns_structured_422(client):
    res = client.get("/tasks/not-a-uuid")
    assert res.status_code == 422
    assert set(res.json()) == {"detail"}


def test_unknown_route_returns_custom_404(client):
    res = client.get("/nope")
    assert res.status_code == 404
    assert res.json() == {"detail": "Route not found: GET /nope"}


def test_wrong_method_returns_json_405(client):
    res = client.put("/tasks")
    assert res.status_code == 405
    assert "detail" in res.json()


def test_filter_by_completed(client):
    done = create(client, title="done").json()
    create(client, title="open")
    client.patch(f"/tasks/{done['id']}", json={"completed": True})

    only_done = client.get("/tasks", params={"completed": True}).json()
    assert [t["title"] for t in only_done["items"]] == ["done"]
    only_open = client.get("/tasks", params={"completed": False}).json()
    assert [t["title"] for t in only_open["items"]] == ["open"]
    assert client.get("/tasks").json()["total"] == 2


def test_pagination_envelope(client):
    for i in range(5):
        create(client, title=f"t{i}")

    page = client.get("/tasks", params={"limit": 2, "offset": 2}).json()
    assert [t["title"] for t in page["items"]] == ["t2", "t3"]
    assert page["total"] == 5
    assert page["next_offset"] == 4
    assert page["previous_offset"] == 0

    last = client.get("/tasks", params={"limit": 2, "offset": 4}).json()
    assert last["next_offset"] is None
    assert client.get("/tasks", params={"limit": 0}).status_code == 422


def test_create_and_delete_are_audit_logged(client, tmp_path):
    task = create(client).json()
    client.delete(f"/tasks/{task['id']}")
    lines = (tmp_path / "audit.log").read_text().splitlines()
    assert len(lines) == 2
    assert "created" in lines[0] and "deleted" in lines[1]
    assert all(task["id"] in line for line in lines)
