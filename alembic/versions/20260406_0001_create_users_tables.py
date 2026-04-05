"""create users tables

Revision ID: 20260406_0001
Revises:
Create Date: 2026-04-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260406_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("roles_json", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_user_profiles_email", "user_profiles", ["email"], unique=True)
    op.create_index("ix_user_profiles_status", "user_profiles", ["status"], unique=False)

    op.create_table(
        "parent_student_links",
        sa.Column("link_id", sa.String(length=64), primary_key=True),
        sa.Column("parent_id", sa.String(length=64), nullable=False),
        sa.Column("student_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_parent_student_links_parent_id",
        "parent_student_links",
        ["parent_id"],
        unique=False,
    )
    op.create_index(
        "ix_parent_student_links_student_id",
        "parent_student_links",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_parent_student_links_status",
        "parent_student_links",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_parent_student_links_status", table_name="parent_student_links")
    op.drop_index("ix_parent_student_links_student_id", table_name="parent_student_links")
    op.drop_index("ix_parent_student_links_parent_id", table_name="parent_student_links")
    op.drop_table("parent_student_links")

    op.drop_index("ix_user_profiles_status", table_name="user_profiles")
    op.drop_index("ix_user_profiles_email", table_name="user_profiles")
    op.drop_table("user_profiles")

