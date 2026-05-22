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
                    "kid": "invite-test-kid",
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
        headers={"kid": "invite-test-kid", "typ": "JWT"},
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


def test_parent_can_create_invite_and_internal_consume_it() -> None:
    client = _client()
    admin_headers = _auth_headers(sub="admin-1", roles=["admin"])

    for user_id, email, display_name, roles in [
        ("parent-1", "parent1@example.com", "Parent One", ["parent"]),
        ("student-1", "student1@example.com", "Student One", ["student"]),
    ]:
        response = client.post(
            "/v1/admin/users",
            json={
                "user_id": user_id,
                "email": email,
                "display_name": display_name,
                "phone": None,
                "roles": roles,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201, response.text

    response = client.post(
        "/v1/admin/links",
        json={"parent_id": "parent-1", "student_id": "student-1", "note": "smoke"},
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text

    invite = client.post(
        "/v1/parent/me/students/student-1/invite",
        json={"ttl_seconds": 3600, "idempotency_key": "invite-1"},
        headers=_auth_headers(sub="parent-1", roles=["parent"]),
    )
    assert invite.status_code == 201, invite.text
    token = invite.json().get("invite_token")
    assert token

    consumed = client.post(
        "/internal/v1/student-invites/consume",
        json={"token": token, "consumer": "auth_service"},
        headers={"X-Service-Token": "internal-token"},
    )
    assert consumed.status_code == 200, consumed.text
    assert consumed.json()["student_user_id"] == "student-1"

    consumed_again = client.post(
        "/internal/v1/student-invites/consume",
        json={"token": token, "consumer": "auth_service"},
        headers={"X-Service-Token": "internal-token"},
    )
    assert consumed_again.status_code == 409, consumed_again.text


def test_internal_consume_requires_service_token() -> None:
    client = _client()
    response = client.post(
        "/internal/v1/student-invites/consume",
        json={"token": "x", "consumer": "auth_service"},
    )
    assert response.status_code == 401
