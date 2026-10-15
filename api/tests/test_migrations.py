"""Tests for Alembic migrations and database schema on test-db."""

import psycopg

from app.config import get_settings

EXPECTED_TABLES = {
    "alembic_version",
    "plans",
    "users",
    "guest_devices",
    "subscriptions",
    "grades",
    "subjects",
    "books",
    "chapters",
    "documents",
    "pages",
    "chunks",
    "practice_items",
    "flashcards",
    "resources",
    "conversations",
    "messages",
    "practice_progress",
    "usage_events",
    "payments",
    "admin_users",
    "audit_log",
}


def test_migrations_tables_and_seeds():
    settings = get_settings()
    with psycopg.connect(settings.TEST_DATABASE_URL) as conn, conn.cursor() as cur:
        # 1. Verify tables
        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        )
        tables = {row[0] for row in cur.fetchall()}
        missing = EXPECTED_TABLES - tables
        assert not missing, f"Missing tables after migration: {missing}"

        # 2. Verify Grades seed
        cur.execute("SELECT id, name_en, name_am FROM grades ORDER BY id;")
        grades = cur.fetchall()
        assert len(grades) == 4
        assert grades[0] == (9, "Grade 9", "9ኛ ክፍል")
        assert grades[3] == (12, "Grade 12", "12ኛ ክፍል")

        # 3. Verify Subjects seed
        cur.execute("SELECT id FROM subjects ORDER BY id;")
        subjects = {r[0] for r in cur.fetchall()}
        expected_subjects = {
            "biology",
            "chemistry",
            "physics",
            "mathematics",
            "english",
            "history",
            "geography",
        }
        assert expected_subjects.issubset(subjects)

        # 4. Verify Plans seed
        cur.execute("SELECT id, price_birr FROM plans ORDER BY id;")
        plans = dict(cur.fetchall())
        assert "free" in plans and plans["free"] == 0.0
        assert "basic" in plans and plans["basic"] == 230.0
        assert "premium" in plans and plans["premium"] == 450.0
        assert "exam_pass" in plans and plans["exam_pass"] == 150.0

        # 5. Verify HNSW index on chunks.embedding
        cur.execute("SELECT indexname FROM pg_indexes WHERE tablename = 'chunks';")
        indexes = {r[0] for r in cur.fetchall()}
        assert "chunks_embedding_idx" in indexes

        # 6. Verify Row Level Security (RLS) is enabled on all tables (except alembic_version)
        cur.execute(
            "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';"
        )
        rls_status = {r[0]: r[1] for r in cur.fetchall()}
        for table in EXPECTED_TABLES - {"alembic_version"}:
            assert rls_status.get(table) is True, f"RLS not enabled on table: {table}"

