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
from src.interface.http.observability import reset_metrics
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
    os.environ["USERS_SERVICE_TOKEN"] = "internal-token"
    reset_metrics()
    get_runtime.cache_clear()
    return TestClient(create_app())


def test_internal_teacher_info_success() -> None:
    client = _client()
    create = client.post(
        "/v1/admin/users",
        json={
            "user_id": "teacher-1",
            "email": "teacher1@example.com",
            "display_name": "Teacher One",
            "phone": None,
            "roles": ["teacher"],
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert create.status_code == 201, create.text

    response = client.get(
        "/internal/v1/teachers/teacher-1",
        headers={"X-Service-Token": "internal-token"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["teacher_id"] == "teacher-1"
    assert body["display_name"] == "Teacher One"


def test_internal_teacher_info_requires_service_token() -> None:
    client = _client()
    response = client.get("/internal/v1/teachers/teacher-1")
    assert response.status_code == 401


def test_internal_teacher_info_returns_404_for_non_teacher() -> None:
    client = _client()
    create = client.post(
        "/v1/admin/users",
        json={
            "user_id": "student-1",
            "email": "student1@example.com",
            "display_name": "Student One",
            "phone": None,
            "roles": ["student"],
        },
        headers=_auth_headers(sub="admin-1", roles=["admin"]),
    )
    assert create.status_code == 201, create.text

    response = client.get(
        "/internal/v1/teachers/student-1",
        headers={"X-Service-Token": "internal-token"},
    )
    assert response.status_code == 404


def test_internal_parent_student_relation_returns_true_for_active_link() -> None:
    client = _client()
    admin_headers = _auth_headers(sub="admin-1", roles=["admin"])

    create_parent = client.post(
        "/v1/admin/users",
        json={
            "user_id": "parent-1",
            "email": "parent1@example.com",
            "display_name": "Parent One",
            "phone": None,
            "roles": ["parent"],
        },
        headers=admin_headers,
    )
    assert create_parent.status_code == 201, create_parent.text

    create_student = client.post(
        "/v1/admin/users",
        json={
            "user_id": "student-1",
            "email": "student1@example.com",
            "display_name": "Student One",
            "phone": None,
            "roles": ["student"],
        },
        headers=admin_headers,
    )
    assert create_student.status_code == 201, create_student.text

    create_link = client.post(
        "/v1/admin/links",
        json={"parent_id": "parent-1", "student_id": "student-1", "note": "smoke"},
        headers=admin_headers,
    )
    assert create_link.status_code == 201, create_link.text

    response = client.get(
        "/internal/v1/parent-students/parent-1/student-1",
        headers={"X-Service-Token": "internal-token"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["has_relation"] is True


def test_internal_parent_student_relation_returns_false_for_missing_link() -> None:
    client = _client()
    response = client.get(
        "/internal/v1/parent-students/parent-404/student-404",
        headers={"X-Service-Token": "internal-token"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "parent_id": "parent-404",
        "student_id": "student-404",
        "has_relation": False,
    }

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert (
        'internal_parent_student_lookup_failures_total{result="not_found"} 1'
        in metrics.text
    )
