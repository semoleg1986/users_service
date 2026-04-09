from __future__ import annotations

from tests.unit.interface.test_api_admin import _auth_headers, _client


def test_user_update_me_route() -> None:
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

    updated = client.patch(
        "/v1/user/me",
        json={"display_name": "Parent Updated"},
        headers=_auth_headers(sub="parent-1", roles=["parent"]),
    )
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Parent Updated"
