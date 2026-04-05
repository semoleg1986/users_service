from __future__ import annotations

from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.wiring import get_runtime


def _client() -> TestClient:
    get_runtime.cache_clear()
    return TestClient(create_app())


def test_healthz() -> None:
    response = _client().get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_admin_create_user_and_link() -> None:
    client = _client()
    create_parent = client.post(
        "/v1/admin/users",
        json={
            "user_id": "parent-1",
            "email": "parent1@example.com",
            "display_name": "Parent 1",
            "phone": "+995555111222",
            "roles": ["parent"],
            "actor_id": "admin-1",
        },
    )
    assert create_parent.status_code == 201, create_parent.text

    create_student = client.post(
        "/v1/admin/users",
        json={
            "user_id": "student-1",
            "email": "student1@example.com",
            "display_name": "Student 1",
            "phone": None,
            "roles": ["student"],
            "actor_id": "admin-1",
        },
    )
    assert create_student.status_code == 201, create_student.text

    create_link = client.post(
        "/v1/admin/links",
        json={
            "parent_id": "parent-1",
            "student_id": "student-1",
            "actor_id": "parent-1",
            "actor_roles": ["parent"],
            "note": "my child",
        },
    )
    assert create_link.status_code == 201, create_link.text
    body = create_link.json()
    assert body["status"] == "active"
    assert body["parent_id"] == "parent-1"
    assert body["student_id"] == "student-1"


def test_admin_create_user_duplicate_email_returns_409() -> None:
    client = _client()
    payload = {
        "user_id": "u-1",
        "email": "dup@example.com",
        "display_name": "User 1",
        "phone": None,
        "roles": ["student"],
        "actor_id": "admin-1",
    }
    first = client.post("/v1/admin/users", json=payload)
    assert first.status_code == 201

    second = client.post("/v1/admin/users", json=payload)
    assert second.status_code == 409
    assert second.headers["content-type"].startswith("application/problem+json")


def test_admin_manage_user_and_links_flow() -> None:
    client = _client()
    client.post(
        "/v1/admin/users",
        json={
            "user_id": "parent-1",
            "email": "parent1@example.com",
            "display_name": "Parent 1",
            "phone": None,
            "roles": ["parent"],
            "actor_id": "admin-1",
        },
    )
    client.post(
        "/v1/admin/users",
        json={
            "user_id": "student-1",
            "email": "student1@example.com",
            "display_name": "Student 1",
            "phone": None,
            "roles": ["student"],
            "actor_id": "admin-1",
        },
    )

    users = client.get("/v1/admin/users", params={"actor_id": "admin-1", "actor_roles": "admin"})
    assert users.status_code == 200
    assert len(users.json()["items"]) == 2

    updated = client.patch(
        "/v1/admin/users/student-1",
        params={"actor_id": "admin-1", "actor_roles": "admin"},
        json={"display_name": "Student 1A"},
    )
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Student 1A"

    assigned = client.post(
        "/v1/admin/users/student-1/roles",
        json={"role": "teacher", "actor_id": "admin-1", "actor_roles": ["admin"]},
    )
    assert assigned.status_code == 200
    assert "teacher" in assigned.json()["roles"]

    blocked = client.post(
        "/v1/admin/users/student-1/block",
        json={"actor_id": "admin-1", "actor_roles": ["admin"]},
    )
    assert blocked.status_code == 200
    assert blocked.json()["status"] == "blocked"

    unblocked = client.post(
        "/v1/admin/users/student-1/unblock",
        json={"actor_id": "admin-1", "actor_roles": ["admin"]},
    )
    assert unblocked.status_code == 200
    assert unblocked.json()["status"] == "active"

    link = client.post(
        "/v1/admin/links",
        json={
            "parent_id": "parent-1",
            "student_id": "student-1",
            "actor_id": "parent-1",
            "actor_roles": ["parent"],
        },
    )
    assert link.status_code == 201
    link_id = link.json()["link_id"]

    links = client.get("/v1/admin/links", params={"actor_id": "admin-1", "actor_roles": "admin"})
    assert links.status_code == 200
    assert len(links.json()["items"]) == 1

    removed = client.request(
        "DELETE",
        f"/v1/admin/links/{link_id}",
        json={"actor_id": "admin-1", "actor_roles": ["admin"]},
    )
    assert removed.status_code == 200
    assert removed.json()["status"] == "removed"


def test_user_me_and_parent_students() -> None:
    client = _client()
    client.post(
        "/v1/admin/users",
        json={
            "user_id": "parent-1",
            "email": "parent1@example.com",
            "display_name": "Parent 1",
            "phone": None,
            "roles": ["parent"],
            "actor_id": "admin-1",
        },
    )
    client.post(
        "/v1/admin/users",
        json={
            "user_id": "student-1",
            "email": "student1@example.com",
            "display_name": "Student 1",
            "phone": None,
            "roles": ["student"],
            "actor_id": "admin-1",
        },
    )
    client.post(
        "/v1/admin/links",
        json={
            "parent_id": "parent-1",
            "student_id": "student-1",
            "actor_id": "parent-1",
            "actor_roles": ["parent"],
        },
    )

    me = client.get(
        "/v1/user/me",
        headers={"X-Actor-Id": "parent-1", "X-Actor-Roles": "parent"},
    )
    assert me.status_code == 200
    assert me.json()["user_id"] == "parent-1"

    students = client.get(
        "/v1/parent/me/students",
        headers={"X-Actor-Id": "parent-1", "X-Actor-Roles": "parent"},
    )
    assert students.status_code == 200
    assert len(students.json()["items"]) == 1
    assert students.json()["items"][0]["user_id"] == "student-1"
