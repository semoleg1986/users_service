from __future__ import annotations

import base64
import json
import os
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.wiring import get_runtime

pytestmark = pytest.mark.integration


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
                    "kid": "itest-kid",
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
        headers={"kid": "itest-kid", "typ": "JWT"},
    )


def _auth_headers(*, sub: str, roles: list[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {_access_token(sub=sub, roles=roles)}"}


def _client() -> TestClient:
    os.environ["USERS_AUTH_JWKS_JSON"] = _jwks_json()
    os.environ["USERS_AUTH_ISSUER"] = "auth_service"
    os.environ["USERS_AUTH_AUDIENCE"] = _AUDIENCE
    get_runtime.cache_clear()
    return TestClient(create_app())


def test_postgres_admin_user_and_links_flow() -> None:
    client = _client()

    parent = client.post(
        "/v1/admin/users",
        json={
            "user_id": "parent-it-1",
            "email": "parent-it-1@example.com",
            "display_name": "Parent IT",
            "phone": "+995555111000",
            "roles": ["parent"],
        },
        headers=_auth_headers(sub="admin-it-1", roles=["admin"]),
    )
    assert parent.status_code == 201, parent.text

    student = client.post(
        "/v1/admin/users",
        json={
            "user_id": "student-it-1",
            "email": "student-it-1@example.com",
            "display_name": "Student IT",
            "phone": None,
            "roles": ["student"],
        },
        headers=_auth_headers(sub="admin-it-1", roles=["admin"]),
    )
    assert student.status_code == 201, student.text

    listed = client.get(
        "/v1/admin/users",
        headers=_auth_headers(sub="admin-it-1", roles=["admin"]),
    )
    assert listed.status_code == 200, listed.text
    assert len(listed.json()["items"]) == 2

    link = client.post(
        "/v1/admin/links",
        json={
            "parent_id": "parent-it-1",
            "student_id": "student-it-1",
            "note": "integration",
        },
        headers=_auth_headers(sub="parent-it-1", roles=["parent"]),
    )
    assert link.status_code == 201, link.text
    link_id = link.json()["link_id"]

    parent_students = client.get(
        "/v1/parent/me/students",
        headers=_auth_headers(sub="parent-it-1", roles=["parent"]),
    )
    assert parent_students.status_code == 200, parent_students.text
    assert parent_students.json()["limit"] == 20
    assert parent_students.json()["offset"] == 0
    assert parent_students.json()["sort"] == "created_at:asc"
    assert len(parent_students.json()["items"]) == 1
    assert parent_students.json()["items"][0]["user_id"] == "student-it-1"

    removed = client.request(
        "DELETE",
        f"/v1/admin/links/{link_id}",
        headers=_auth_headers(sub="admin-it-1", roles=["admin"]),
    )
    assert removed.status_code == 200, removed.text
    assert removed.json()["status"] == "removed"
