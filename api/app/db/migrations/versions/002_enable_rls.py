"""Enable Row Level Security (RLS) on all application tables.

Revision ID: 002_enable_rls
Revises: 001_initial_schema
Create Date: 2026-10-15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "002_enable_rls"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = [
    "admin_users",
    "audit_log",
    "books",
    "chapters",
    "chunks",
    "conversations",
    "documents",
    "flashcards",
    "grades",
    "guest_devices",
    "messages",
    "pages",
    "payments",
    "plans",
    "practice_items",
    "practice_progress",
    "resources",
    "subjects",
    "subscriptions",
    "usage_events",
    "users",
]


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
