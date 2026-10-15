"""Initial schema creation with pgvector and seed data.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 0. Ensure pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. Plans
    op.create_table(
        "plans",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price_birr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("period_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("questions_per_day", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("monthly_voice_chars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_upload_chars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cloud_stt", sa.Boolean(), nullable=False, server_default="false"),
    )

    # 2. Grades & Subjects
    op.create_table(
        "grades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name_en", sa.String(), nullable=False),
        sa.Column("name_am", sa.String(), nullable=False),
    )

    op.create_table(
        "subjects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name_en", sa.String(), nullable=False),
        sa.Column("name_am", sa.String(), nullable=False),
    )

    # 3. Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("phone", sa.String(), unique=True, index=True, nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("grade", sa.Integer(), nullable=True),
        sa.Column("preferred_lang", sa.String(), nullable=False, server_default="am"),
        sa.Column(
            "plan_id", sa.String(), sa.ForeignKey("plans.id"), nullable=False, server_default="free"
        ),
        sa.Column("free_questions_left", sa.Integer(), nullable=False, server_default="5"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 4. Guest Devices
    op.create_table(
        "guest_devices",
        sa.Column("device_token", sa.String(), primary_key=True, index=True),
        sa.Column("ip", sa.String(), nullable=True),
        sa.Column("questions_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
    )

    # 5. Subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.String(), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payment_id", sa.String(), nullable=True),
    )

    # 6. Books & Chapters
    op.create_table(
        "books",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("subject_id", sa.String(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("grade_id", sa.Integer(), sa.ForeignKey("grades.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("edition", sa.String(), nullable=False, server_default="2026"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("source", sa.String(), nullable=False, server_default="moe"),
        sa.Column("permission_note", sa.Text(), nullable=True),
    )

    op.create_table(
        "chapters",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("book_id", sa.String(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title_en", sa.String(), nullable=False),
        sa.Column("title_am", sa.String(), nullable=False),
        sa.Column("first_page", sa.Integer(), nullable=False),
        sa.Column("last_page", sa.Integer(), nullable=False),
    )

    # 7. Documents, Pages, Chunks
    op.create_table(
        "documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("owner_type", sa.String(), nullable=False, server_default="library"),
        sa.Column("owner_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("book_id", sa.String(), sa.ForeignKey("books.id"), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("text_hash", sa.String(), index=True, nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="processing"),
    )

    op.create_table(
        "pages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("page_no", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
    )
    op.create_index("ix_pages_doc_page", "pages", ["document_id", "page_no"])

    op.create_table(
        "chunks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("chapter_id", sa.String(), sa.ForeignKey("chapters.id"), nullable=True),
        sa.Column("page_no", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding", Vector(1024), nullable=True),
    )
    op.create_index("chunks_document_idx", "chunks", ["document_id"])
    op.create_index("chunks_chapter_idx", "chunks", ["chapter_id"])
    # HNSW cosine index for pgvector
    op.execute(
        "CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);"
    )

    # 8. Practice Items & Flashcards
    op.create_table(
        "practice_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "chapter_id", sa.String(), sa.ForeignKey("chapters.id"), nullable=True, index=True
        ),
        sa.Column(
            "document_id", sa.String(), sa.ForeignKey("documents.id"), nullable=True, index=True
        ),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="generated"),
        sa.Column("hidden", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.create_table(
        "flashcards",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "chapter_id", sa.String(), sa.ForeignKey("chapters.id"), nullable=True, index=True
        ),
        sa.Column(
            "document_id", sa.String(), sa.ForeignKey("documents.id"), nullable=True, index=True
        ),
        sa.Column("front", sa.Text(), nullable=False),
        sa.Column("back_am", sa.Text(), nullable=False),
        sa.Column("back_en", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
    )

    op.create_table(
        "resources",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "chapter_id", sa.String(), sa.ForeignKey("chapters.id"), nullable=False, index=True
        ),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False, server_default="am"),
        sa.Column("minutes", sa.Integer(), nullable=True),
    )

    # 9. Conversations & Messages
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("scope_type", sa.String(), nullable=False),
        sa.Column("scope_id", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(),
            sa.ForeignKey("conversations.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("answer_lang", sa.String(), nullable=False, server_default="am"),
        sa.Column("input_method", sa.String(), nullable=False, server_default="keyboard"),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("speech_script", sa.Text(), nullable=True),
        sa.Column("audio_url", sa.String(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 10. Progress, Usage, Payments
    op.create_table(
        "practice_progress",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column(
            "item_id", sa.String(), sa.ForeignKey("practice_items.id"), nullable=False, index=True
        ),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("ease", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "due_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "usage_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("device_token", sa.String(), nullable=True, index=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("units_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("units_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("amount_birr", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("chapa_tx_ref", sa.String(), unique=True, index=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 11. Admin users & Audit Log
    op.create_table(
        "admin_users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="editor"),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("admin_id", sa.String(), sa.ForeignKey("admin_users.id"), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 12. Seed initial data
    # Seed Plans
    op.execute(
        """
        INSERT INTO plans (id, name, price_birr, period_days, questions_per_day, monthly_voice_chars, max_upload_chars, cloud_stt) VALUES
        ('free', 'Free', 0.0, 30, 5, 0, 0, false),
        ('basic', 'Basic', 230.0, 30, 10, 0, 900000, false),
        ('premium', 'Premium', 450.0, 30, 20, 120000, 1800000, true),
        ('exam_pass', 'Exam Pass (7-day)', 150.0, 7, 20, 60000, 900000, true)
        ON CONFLICT (id) DO NOTHING;
        """
    )

    # Seed Grades (9 to 12)
    op.execute(
        """
        INSERT INTO grades (id, name_en, name_am) VALUES
        (9, 'Grade 9', '9ኛ ክፍል'),
        (10, 'Grade 10', '10ኛ ክፍል'),
        (11, 'Grade 11', '11ኛ ክፍል'),
        (12, 'Grade 12', '12ኛ ክፍል')
        ON CONFLICT (id) DO NOTHING;
        """
    )

    # Seed Core Curriculum Subjects
    op.execute(
        """
        INSERT INTO subjects (id, name_en, name_am) VALUES
        ('biology', 'Biology', 'ባዮሎጂ'),
        ('chemistry', 'Chemistry', 'ኬሚስትሪ'),
        ('physics', 'Physics', 'ፊዚክስ'),
        ('mathematics', 'Mathematics', 'ሒሳብ'),
        ('english', 'English', 'እንግሊዝኛ'),
        ('history', 'History', 'ታሪክ'),
        ('geography', 'Geography', 'ጂኦግራፊ')
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade() -> None:
    tables = [
        "audit_log",
        "admin_users",
        "payments",
        "usage_events",
        "practice_progress",
        "messages",
        "conversations",
        "resources",
        "flashcards",
        "practice_items",
        "chunks",
        "pages",
        "documents",
        "chapters",
        "books",
        "subscriptions",
        "guest_devices",
        "users",
        "subjects",
        "grades",
        "plans",
    ]
    for table in tables:
        op.drop_table(table)
