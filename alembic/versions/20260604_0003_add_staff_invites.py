"""add staff invites table

Revision ID: 20260604_0003
Revises: 20260522_0002
Create Date: 2026-06-04
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260604_0003"
down_revision: Union[str, Sequence[str], None] = "20260522_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "staff_invites",
        sa.Column("invite_id", sa.String(length=64), primary_key=True),
        sa.Column("creator_user_id", sa.String(length=64), nullable=False),
        sa.Column("target_user_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("roles_json", sa.Text(), nullable=False),
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
        "ix_staff_invites_creator_user_id",
        "staff_invites",
        ["creator_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_staff_invites_target_user_id",
        "staff_invites",
        ["target_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_staff_invites_status",
        "staff_invites",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_staff_invites_token_hash",
        "staff_invites",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_staff_invites_token_hash", table_name="staff_invites")
    op.drop_index("ix_staff_invites_status", table_name="staff_invites")
    op.drop_index("ix_staff_invites_target_user_id", table_name="staff_invites")
    op.drop_index("ix_staff_invites_creator_user_id", table_name="staff_invites")
    op.drop_table("staff_invites")
