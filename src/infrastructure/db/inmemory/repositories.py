"""In-memory репозитории users_service."""

from __future__ import annotations

from datetime import UTC, datetime

from src.domain.links.parent_student_link.entity import ParentStudentLink
from src.domain.links.student_invite.entity import StudentInvite
from src.domain.shared.statuses import InviteStatus
from src.domain.users.profile.entity import UserProfile


class InMemoryUserProfileRepository:
    """In-memory репозиторий UserProfile."""

    def __init__(self) -> None:
        self._by_id: dict[str, UserProfile] = {}
        self._by_email: dict[str, str] = {}

    def get(self, user_id: str) -> UserProfile | None:
        return self._by_id.get(user_id)

    def get_by_email(self, email: str) -> UserProfile | None:
        user_id = self._by_email.get(email.strip().lower())
        if user_id is None:
            return None
        return self._by_id.get(user_id)

    def save(self, profile: UserProfile) -> None:
        self._by_id[profile.user_id] = profile
        self._by_email[profile.email.value] = profile.user_id

    def list(
        self, *, role: str | None = None, status: str | None = None
    ) -> list[UserProfile]:
        items = list(self._by_id.values())
        if role is not None:
            items = [p for p in items if role in {r.value for r in p.roles}]
        if status is not None:
            items = [p for p in items if p.status.value == status]
        return sorted(items, key=lambda p: p.meta.created_at)


class InMemoryParentStudentLinkRepository:
    """In-memory репозиторий ParentStudentLink."""

    def __init__(self) -> None:
        self._by_id: dict[str, ParentStudentLink] = {}
        self._by_pair: dict[tuple[str, str], str] = {}

    def get(self, link_id: str) -> ParentStudentLink | None:
        return self._by_id.get(link_id)

    def get_active_by_pair(
        self, parent_id: str, student_id: str
    ) -> ParentStudentLink | None:
        link_id = self._by_pair.get((parent_id, student_id))
        if link_id is None:
            return None
        link = self._by_id.get(link_id)
        if link is None:
            return None
        return link if link.status.value == "active" else None

    def save(self, link: ParentStudentLink) -> None:
        self._by_id[link.link_id] = link
        if link.status.value == "active":
            self._by_pair[(link.parent_id, link.student_id)] = link.link_id
        else:
            self._by_pair.pop((link.parent_id, link.student_id), None)

    def list(
        self, *, parent_id: str | None = None, student_id: str | None = None
    ) -> list[ParentStudentLink]:
        items = list(self._by_id.values())
        if parent_id is not None:
            items = [i for i in items if i.parent_id == parent_id]
        if student_id is not None:
            items = [i for i in items if i.student_id == student_id]
        return sorted(items, key=lambda i: i.meta.created_at)

    def list_active_by_parent(self, parent_id: str) -> list[ParentStudentLink]:
        return [
            i
            for i in self._by_id.values()
            if i.parent_id == parent_id and i.status.value == "active"
        ]


class InMemoryStudentInviteRepository:
    """In-memory репозиторий StudentInvite."""

    def __init__(self) -> None:
        self._by_id: dict[str, StudentInvite] = {}
        self._by_token_hash: dict[str, str] = {}
        self._by_parent_idempotency: dict[tuple[str, str], str] = {}

    def get(self, invite_id: str) -> StudentInvite | None:
        return self._by_id.get(invite_id)

    def get_by_parent_and_idempotency(
        self, *, parent_id: str, idempotency_key: str
    ) -> StudentInvite | None:
        invite_id = self._by_parent_idempotency.get((parent_id, idempotency_key))
        if invite_id is None:
            return None
        return self._by_id.get(invite_id)

    def get_pending_by_student(self, student_id: str) -> StudentInvite | None:
        now = datetime.now(UTC)
        for invite in self._by_id.values():
            if invite.student_user_id != student_id:
                continue
            invite.mark_expired_if_needed(now=now, actor_id="system")
            if invite.status == InviteStatus.PENDING:
                return invite
        return None

    def get_by_token_hash(self, token_hash: str) -> StudentInvite | None:
        invite_id = self._by_token_hash.get(token_hash)
        if invite_id is None:
            return None
        return self._by_id.get(invite_id)

    def save(self, invite: StudentInvite) -> None:
        self._by_id[invite.invite_id] = invite
        self._by_token_hash[invite.token_hash.value] = invite.invite_id
        if invite.idempotency_key is not None:
            self._by_parent_idempotency[
                (invite.parent_user_id, invite.idempotency_key.value)
            ] = invite.invite_id
