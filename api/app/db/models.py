"""SQLAlchemy models for all 21 data model tables defined in architecture spec."""

import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String, primary_key=True)  # e.g., 'free', 'basic', 'premium', 'exam_pass'
    name = Column(String, nullable=False)
    price_birr = Column(Float, nullable=False, default=0.0)
    period_days = Column(Integer, nullable=False, default=30)
    questions_per_day = Column(Integer, nullable=False, default=10)
    monthly_voice_chars = Column(Integer, nullable=False, default=0)
    max_upload_chars = Column(Integer, nullable=False, default=0)
    cloud_stt = Column(Boolean, nullable=False, default=False)

    users = relationship("User", back_populates="plan")
    subscriptions = relationship("Subscription", back_populates="plan")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    phone = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    grade = Column(Integer, nullable=True)
    preferred_lang = Column(String, default="am", nullable=False)
    plan_id = Column(String, ForeignKey("plans.id"), default="free", nullable=False)
    free_questions_left = Column(Integer, default=5, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    plan = relationship("Plan", back_populates="users")
    guest_devices = relationship("GuestDevice", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    documents = relationship("Document", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class GuestDevice(Base):
    __tablename__ = "guest_devices"

    device_token = Column(String, primary_key=True, index=True)
    ip = Column(String, nullable=True)
    questions_used = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    user = relationship("User", back_populates="guest_devices")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    payment_id = Column(String, nullable=True)

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True)
    name_en = Column(String, nullable=False)
    name_am = Column(String, nullable=False)

    books = relationship("Book", back_populates="grade")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String, primary_key=True)
    name_en = Column(String, nullable=False)
    name_am = Column(String, nullable=False)

    books = relationship("Book", back_populates="subject")


class Book(Base):
    __tablename__ = "books"

    id = Column(String, primary_key=True, default=generate_uuid)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    grade_id = Column(Integer, ForeignKey("grades.id"), nullable=False)
    title = Column(String, nullable=False)
    edition = Column(String, default="2026", nullable=False)
    status = Column(String, default="active", nullable=False)  # active, retired
    source = Column(String, default="moe", nullable=False)
    permission_note = Column(Text, nullable=True)

    subject = relationship("Subject", back_populates="books")
    grade = relationship("Grade", back_populates="books")
    chapters = relationship("Chapter", back_populates="book")
    documents = relationship("Document", back_populates="book")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String, primary_key=True, default=generate_uuid)
    book_id = Column(String, ForeignKey("books.id"), nullable=False)
    number = Column(Integer, nullable=False)
    title_en = Column(String, nullable=False)
    title_am = Column(String, nullable=False)
    first_page = Column(Integer, nullable=False)
    last_page = Column(Integer, nullable=False)

    book = relationship("Book", back_populates="chapters")
    chunks = relationship("Chunk", back_populates="chapter")
    practice_items = relationship("PracticeItem", back_populates="chapter")
    flashcards = relationship("Flashcard", back_populates="chapter")
    resources = relationship("Resource", back_populates="chapter")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    owner_type = Column(String, default="library", nullable=False)  # library or user
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)
    book_id = Column(String, ForeignKey("books.id"), nullable=True)
    title = Column(String, nullable=False)
    page_count = Column(Integer, default=0, nullable=False)
    text_hash = Column(String, index=True, nullable=True)
    status = Column(String, default="processing", nullable=False)  # processing, ready, failed

    user = relationship("User", back_populates="documents")
    book = relationship("Book", back_populates="documents")
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    page_no = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    document = relationship("Document", back_populates="pages")

    __table_args__ = (Index("ix_pages_doc_page", "document_id", "page_no"),)


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True, index=True)
    page_no = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    embedding = Column(Vector(1024), nullable=True)

    document = relationship("Document", back_populates="chunks")
    chapter = relationship("Chapter", back_populates="chunks")

    __table_args__ = (
        Index("chunks_document_idx", "document_id"),
        Index("chunks_chapter_idx", "chapter_id"),
    )


class PracticeItem(Base):
    __tablename__ = "practice_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True, index=True)
    type = Column(String, nullable=False)  # multiple_choice, short_answer
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)  # List of string options
    answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    page = Column(Integer, nullable=False)
    source = Column(String, default="generated", nullable=False)  # generated, exercise, past_exam
    hidden = Column(Boolean, default=False, nullable=False)

    chapter = relationship("Chapter", back_populates="practice_items")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(String, primary_key=True, default=generate_uuid)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True, index=True)
    front = Column(Text, nullable=False)
    back_am = Column(Text, nullable=False)
    back_en = Column(Text, nullable=False)
    page = Column(Integer, nullable=False)

    chapter = relationship("Chapter", back_populates="flashcards")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String, primary_key=True, default=generate_uuid)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)  # video, link, past_paper
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    language = Column(String, default="am", nullable=False)
    minutes = Column(Integer, nullable=True)

    chapter = relationship("Chapter", back_populates="resources")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    scope_type = Column(String, nullable=False)  # chapter, book, subject, document
    scope_id = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant
    text = Column(Text, nullable=False)
    answer_lang = Column(String, default="am", nullable=False)
    input_method = Column(String, default="keyboard", nullable=False)  # keyboard, speech, cloud_stt
    citations = Column(JSON, nullable=True)  # [{"book": "...", "page": 45}]
    speech_script = Column(Text, nullable=True)
    audio_url = Column(String, nullable=True)
    rating = Column(Integer, nullable=True)  # 1 for thumbs up, -1 for thumbs down
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class PracticeProgress(Base):
    __tablename__ = "practice_progress"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(String, ForeignKey("practice_items.id"), nullable=False, index=True)
    correct = Column(Boolean, nullable=False)
    ease = Column(Float, default=2.5, nullable=False)
    interval_days = Column(Integer, default=1, nullable=False)
    due_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    device_token = Column(String, nullable=True, index=True)
    kind = Column(String, nullable=False)  # chat, embed, practice, speech_script, tts, stt
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    units_in = Column(Integer, default=0, nullable=False)
    units_out = Column(Integer, default=0, nullable=False)
    cost_usd = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount_birr = Column(Float, nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, success, failed
    chapa_tx_ref = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="payments")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="editor", nullable=False)  # superadmin, editor, viewer
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    audit_logs = relationship("AuditLog", back_populates="admin")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=generate_uuid)
    admin_id = Column(String, ForeignKey("admin_users.id"), nullable=True)
    action = Column(String, nullable=False)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    admin = relationship("AdminUser", back_populates="audit_logs")
