"""add student invites table

Revision ID: 20260522_0002
Revises: 20260406_0001
Create Date: 2026-05-22
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260522_0002"
down_revision: Union[str, Sequence[str], None] = "20260406_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "student_invites",
        sa.Column("invite_id", sa.String(length=64), primary_key=True),
        sa.Column("parent_user_id", sa.String(length=64), nullable=False),
        sa.Column("student_user_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_student_invites_parent_user_id",
        "student_invites",
        ["parent_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_student_invites_student_user_id",
        "student_invites",
        ["student_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_student_invites_status",
        "student_invites",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_student_invites_token_hash",
        "student_invites",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_student_invites_token_hash", table_name="student_invites")
    op.drop_index("ix_student_invites_status", table_name="student_invites")
    op.drop_index("ix_student_invites_student_user_id", table_name="student_invites")
    op.drop_index("ix_student_invites_parent_user_id", table_name="student_invites")
    op.drop_table("student_invites")
