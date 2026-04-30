from __future__ import annotations

import base64
import json
import os
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.wiring import get_runtime

_PRIVATE_KEY = Ed25519PrivateKey.generate()
_PUBLIC_KEY = _PRIVATE_KEY.public_key()
_AUDIENCE = "platform_clients"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _jwks_json() -> str:
    raw = _PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return json.dumps(
        {
            "keys": [
                {
                    "kty": "OKP",
                    "crv": "Ed25519",
                    "x": _b64url(raw),
                    "alg": "EdDSA",
                    "use": "sig",
                    "kid": "test-kid",
                }
            ]
        }
    )


def _access_token(*, sub: str, roles: list[str]) -> str:
    now = datetime.now(UTC)
    claims = {
        "iss": "auth_service",
        "aud": _AUDIENCE,
        "typ": "access",
        "sub": sub,
        "jti": f"jti-{sub}",
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(
        claims,
        _PRIVATE_KEY,
        algorithm="EdDSA",
        headers={"kid": "test-kid", "typ": "JWT"},
    )


def _auth_headers(*, sub: str, roles: list[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {_access_token(sub=sub, roles=roles)}"}


def _client() -> TestClient:
    os.environ["USERS_AUTH_JWKS_JSON"] = _jwks_json()
    os.environ["USERS_AUTH_ISSUER"] = "auth_service"
    os.environ["USERS_AUTH_AUDIENCE"] = _AUDIENCE
    get_runtime.cache_clear()
    return TestClient(create_app())


def test_healthz() -> None:
    response = _client().get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_endpoint_exposes_prometheus_metrics() -> None:
    response = _client().get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
    assert "http_errors_total" in response.text


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
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
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
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert create_student.status_code == 201, create_student.text

    create_link = client.post(
        "/v1/admin/links",
        json={
            "parent_id": "parent-1",
            "student_id": "student-1",
            "note": "my child",
        },
        headers=_auth_headers(sub="parent-1", roles=["parent"]),
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
    }
    first = client.post(
        "/v1/admin/users",
        json=payload,
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert first.status_code == 201

    second = client.post(
        "/v1/admin/users",
        json=payload,
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
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
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    client.post(
        "/v1/admin/users",
        json={
            "user_id": "student-1",
            "email": "student1@example.com",
            "display_name": "Student 1",
            "phone": None,
            "roles": ["student"],
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )

    users = client.get(
        "/v1/admin/users",
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert users.status_code == 200
    assert len(users.json()["items"]) == 2

    updated = client.patch(
        "/v1/admin/users/student-1",
        json={"display_name": "Student 1A"},
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Student 1A"

    assigned = client.post(
        "/v1/admin/users/student-1/roles",
        json={"role": "teacher"},
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert assigned.status_code == 200
    assert "teacher" in assigned.json()["roles"]

    blocked = client.post(
        "/v1/admin/users/student-1/block",
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert blocked.status_code == 200
    assert blocked.json()["status"] == "blocked"

    unblocked = client.post(
        "/v1/admin/users/student-1/unblock",
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert unblocked.status_code == 200
    assert unblocked.json()["status"] == "active"

    link = client.post(
        "/v1/admin/links",
        json={
            "parent_id": "parent-1",
            "student_id": "student-1",
        },
        headers=_auth_headers(sub="parent-1", roles=["parent"]),
    )
    assert link.status_code == 201
    link_id = link.json()["link_id"]

    links = client.get(
        "/v1/admin/links",
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert links.status_code == 200
    assert len(links.json()["items"]) == 1

    removed = client.request(
        "DELETE",
        f"/v1/admin/links/{link_id}",
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
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
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    client.post(
        "/v1/admin/users",
        json={
            "user_id": "student-1",
            "email": "student1@example.com",
            "display_name": "Student 1",
            "phone": None,
            "roles": ["student"],
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    client.post(
        "/v1/admin/links",
        json={
            "parent_id": "parent-1",
            "student_id": "student-1",
        },
        headers=_auth_headers(sub="parent-1", roles=["parent"]),
    )

    me = client.get(
        "/v1/user/me",
        headers=_auth_headers(sub="parent-1", roles=["parent"]),
    )
    assert me.status_code == 200
    assert me.json()["user_id"] == "parent-1"

    students = client.get(
        "/v1/parent/me/students",
        headers=_auth_headers(sub="parent-1", roles=["parent"]),
    )
    assert students.status_code == 200
    assert len(students.json()["items"]) == 1
    assert students.json()["items"][0]["user_id"] == "student-1"


def test_revoke_last_active_admin_role_is_forbidden() -> None:
    client = _client()
    create_admin_1 = client.post(
        "/v1/admin/users",
        json={
            "user_id": "admin-1",
            "email": "admin1@example.com",
            "display_name": "Admin 1",
            "phone": None,
            "roles": ["admin"],
        },
        headers=_auth_headers(sub="root-admin", roles=["admin"]),
    )
    assert create_admin_1.status_code == 201, create_admin_1.text

    revoke_last = client.delete(
        "/v1/admin/users/admin-1/roles?role=admin",
        headers=_auth_headers(sub="root-admin", roles=["admin"]),
    )
    assert revoke_last.status_code == 409
    assert revoke_last.headers["content-type"].startswith("application/problem+json")
    assert "последнего активного admin" in revoke_last.json()["detail"]

    create_admin_2 = client.post(
        "/v1/admin/users",
        json={
            "user_id": "admin-2",
            "email": "admin2@example.com",
            "display_name": "Admin 2",
            "phone": None,
            "roles": ["admin"],
        },
        headers=_auth_headers(sub="root-admin", roles=["admin"]),
    )
    assert create_admin_2.status_code == 201, create_admin_2.text

    assign_teacher = client.post(
        "/v1/admin/users/admin-1/roles",
        json={"role": "teacher"},
        headers=_auth_headers(sub="root-admin", roles=["admin"]),
    )
    assert assign_teacher.status_code == 200, assign_teacher.text

    revoke_not_last = client.delete(
        "/v1/admin/users/admin-1/roles?role=admin",
        headers=_auth_headers(sub="root-admin", roles=["admin"]),
    )
    assert revoke_not_last.status_code == 200, revoke_not_last.text
    assert "admin" not in revoke_not_last.json()["roles"]


def test_block_or_archive_last_active_admin_is_forbidden() -> None:
    client = _client()
    create_admin_1 = client.post(
        "/v1/admin/users",
        json={
            "user_id": "admin-1",
            "email": "admin1@example.com",
            "display_name": "Admin 1",
            "phone": None,
            "roles": ["admin"],
        },
        headers=_auth_headers(sub="root-admin", roles=["admin"]),
    )
    assert create_admin_1.status_code == 201, create_admin_1.text

    block_last = client.post(
        "/v1/admin/users/admin-1/block",
        headers=_auth_headers(sub="root-admin", roles=["admin"]),
    )
    assert block_last.status_code == 409
    assert block_last.headers["content-type"].startswith("application/problem+json")
    assert "последнего активного admin" in block_last.json()["detail"]

    archive_last = client.post(
        "/v1/admin/users/admin-1/archive",
        headers=_auth_headers(sub="root-admin", roles=["admin"]),
    )
    assert archive_last.status_code == 409
    assert archive_last.headers["content-type"].startswith("application/problem+json")
    assert "последнего активного admin" in archive_last.json()["detail"]


def test_admin_create_link_rejects_invalid_roles_and_non_active_profiles() -> None:
    client = _client()
    create_teacher = client.post(
        "/v1/admin/users",
        json={
            "user_id": "teacher-1",
            "email": "teacher1@example.com",
            "display_name": "Teacher 1",
            "phone": None,
            "roles": ["teacher"],
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert create_teacher.status_code == 201, create_teacher.text

    create_student = client.post(
        "/v1/admin/users",
        json={
            "user_id": "student-1",
            "email": "student1@example.com",
            "display_name": "Student 1",
            "phone": None,
            "roles": ["student"],
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert create_student.status_code == 201, create_student.text

    invalid_roles_link = client.post(
        "/v1/admin/links",
        json={
            "parent_id": "teacher-1",
            "student_id": "student-1",
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert invalid_roles_link.status_code == 409

    create_parent = client.post(
        "/v1/admin/users",
        json={
            "user_id": "parent-1",
            "email": "parent1@example.com",
            "display_name": "Parent 1",
            "phone": None,
            "roles": ["parent"],
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert create_parent.status_code == 201, create_parent.text

    blocked = client.post(
        "/v1/admin/users/student-1/block",
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert blocked.status_code == 200, blocked.text

    non_active_link = client.post(
        "/v1/admin/links",
        json={
            "parent_id": "parent-1",
            "student_id": "student-1",
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert non_active_link.status_code == 409
