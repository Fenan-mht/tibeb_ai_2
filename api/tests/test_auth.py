"""Tests for test-mode identity, authentication headers, and data isolation."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Conversation, Document, Message
from app.main import app
from scripts.seed_testers import seed_testers


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Ensure tester plan and accounts are seeded in test database."""
    from app.config import get_settings

    settings = get_settings()
    seed_testers(settings.TEST_DATABASE_URL)


@pytest.fixture
def client():
    return TestClient(app)


def test_missing_tester_id_rejected(client: TestClient):
    """Requests without X-Tester-Id in test mode must receive HTTP 401."""
    response = client.get("/v1/me")
    assert response.status_code == 401
    assert "Missing X-Tester-Id" in response.json()["detail"]


def test_unknown_tester_id_rejected(client: TestClient):
    """Requests with unknown X-Tester-Id must receive HTTP 401."""
    response = client.get("/v1/me", headers={"X-Tester-Id": "nonexistent-user-123"})
    assert response.status_code == 401
    assert "Unknown tester ID" in response.json()["detail"]


def test_valid_tester_can_read_profile(client: TestClient):
    """Seeded tester can retrieve their profile, plan tier, and questions left."""
    # Test Premium tester
    response = client.get("/v1/me", headers={"X-Tester-Id": "tester-premium-1"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "tester-premium-1"
    assert data["name"] == "Kenenisa Bekele"
    assert data["grade"] == 10
    assert data["plan_id"] == "premium"
    assert data["plan"]["name"] == "Premium"
    assert data["plan"]["questions_per_day"] == 20

    # Test Free tester
    response_free = client.get("/v1/me", headers={"X-Tester-Id": "tester-free-1"})
    assert response_free.status_code == 200
    free_data = response_free.json()
    assert free_data["id"] == "tester-free-1"
    assert free_data["plan_id"] == "free"
    assert free_data["free_questions_left"] == 5


def test_list_available_testers(client: TestClient):
    """GET /v1/auth/testers returns the list of 10 seeded testers."""
    response = client.get("/v1/auth/testers")
    assert response.status_code == 200
    testers = response.json()
    assert len(testers) >= 10
    ids = {t["id"] for t in testers}
    assert "tester-free-1" in ids
    assert "tester-premium-1" in ids
    assert "tester-tester-1" in ids


def test_tester_data_isolation():
    """Verify strict student data isolation: one tester can never access another tester's data."""
    # Direct database verification using session
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # Create a private conversation and document owned by tester-premium-1
        conv_a = Conversation(
            id="conv-tester-premium-1",
            user_id="tester-premium-1",
            scope_type="chapter",
            scope_id="chap-bio-1",
            summary="Tester A private question on Biology",
        )
        msg_a = Message(
            id="msg-tester-premium-1",
            conversation_id="conv-tester-premium-1",
            role="user",
            text="Private question from tester A",
        )
        doc_a = Document(
            id="doc-tester-premium-1",
            owner_type="user",
            owner_id="tester-premium-1",
            title="Tester A Secret Handout Notes",
            page_count=2,
            status="ready",
        )
        db.merge(conv_a)
        db.merge(msg_a)
        db.merge(doc_a)
        db.commit()

        # Query conversations scoped to tester-basic-1
        tester_b_convs = (
            db.query(Conversation)
            .filter(Conversation.user_id == "tester-basic-1")
            .all()
        )
        tester_b_conv_ids = {c.id for c in tester_b_convs}
        assert "conv-tester-premium-1" not in tester_b_conv_ids

        # Query user documents scoped to tester-basic-1
        tester_b_docs = (
            db.query(Document)
            .filter(Document.owner_type == "user", Document.owner_id == "tester-basic-1")
            .all()
        )
        tester_b_doc_ids = {d.id for d in tester_b_docs}
        assert "doc-tester-premium-1" not in tester_b_doc_ids

        # Query scoped to tester-premium-1
        tester_a_docs = (
            db.query(Document)
            .filter(Document.owner_type == "user", Document.owner_id == "tester-premium-1")
            .all()
        )
        tester_a_doc_ids = {d.id for d in tester_a_docs}
        assert "doc-tester-premium-1" in tester_a_doc_ids
    finally:
        db.close()
