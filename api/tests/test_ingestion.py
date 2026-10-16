"""Tests for library ingestion, PDF extraction, chunking, and deduplication."""

from pathlib import Path

import fitz
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db.models import Chapter, Chunk, Page
from app.providers.fakes import FakeEmbedder
from app.services.ingestion import (
    ExtractedPage,
    ScannedPDFError,
    chunk_document_pages,
    clean_text,
    extract_pages_from_pdf,
    ingest_textbook,
)


def create_sample_pdf(file_path: Path, pages_content: list[str]) -> Path:
    """Helper to generate a real PDF using PyMuPDF for testing."""
    doc = fitz.open()
    for text in pages_content:
        page = doc.new_page()
        # insert text at point (50, 72)
        page.insert_text(fitz.Point(50, 72), text)
    doc.save(str(file_path))
    doc.close()
    return file_path


def test_clean_text_fixes_hyphenation_and_whitespace():
    """Verify clean_text fixes broken hyphenation and collapses whitespace."""
    raw = "Pho-\ntosynthesis is a process in which light en-\nergy is converted."
    cleaned = clean_text(raw)
    assert "Photosynthesis" in cleaned
    assert "energy" in cleaned
    assert "Pho-\ntosynthesis" not in cleaned


def test_chunking_never_crosses_page_boundaries():
    """CRITICAL RULE: Chunks must strictly stay within single page boundaries."""
    # Generate 3 long pages of text
    long_p1 = "Page one content. " * 150  # ~450 words / ~600 tokens
    long_p2 = "Page two unique biology facts. " * 180  # ~900 words
    long_p3 = "Page three chemistry experiments. " * 120

    extracted = [
        ExtractedPage(page_no=1, text=long_p1, char_count=len(long_p1)),
        ExtractedPage(page_no=2, text=long_p2, char_count=len(long_p2)),
        ExtractedPage(page_no=3, text=long_p3, char_count=len(long_p3)),
    ]

    chunks = chunk_document_pages(extracted, min_tokens=300, max_tokens=500)
    assert len(chunks) > 3, "Expected multiple chunks for long pages"

    for chunk in chunks:
        # Every chunk must belong to exactly one page
        assert chunk.page_no in {1, 2, 3}
        if chunk.page_no == 1:
            assert "Page one content" in chunk.text
            assert "Page two" not in chunk.text
            assert "Page three" not in chunk.text
        elif chunk.page_no == 2:
            assert "Page two unique biology" in chunk.text
            assert "Page one" not in chunk.text
            assert "Page three" not in chunk.text
        elif chunk.page_no == 3:
            assert "Page three chemistry" in chunk.text
            assert "Page one" not in chunk.text
            assert "Page two" not in chunk.text


def test_scanned_pdf_is_detected_and_rejected(tmp_path: Path):
    """Scanned PDFs (>30% of pages with <50 chars) must be reported and rejected."""
    scanned_pdf_path = tmp_path / "scanned_sample.pdf"
    # Create 4 pages where 3 pages are blank / image-only (under 50 chars)
    pages = [
        "A regular page with sufficient text over fifty characters long to pass.",
        "p2",  # scanned / empty
        "p3",  # scanned / empty
        "",    # scanned / empty
    ]
    create_sample_pdf(scanned_pdf_path, pages)

    with pytest.raises(ScannedPDFError) as exc_info:
        extract_pages_from_pdf(scanned_pdf_path)

    assert "Scanned PDF detected" in str(exc_info.value)
    assert "fewer than 50 characters" in str(exc_info.value)


def test_ingest_textbook_end_to_end_and_deduplication(tmp_path: Path):
    """Verify full textbook ingestion, vector embeddings, and text_hash skipping."""
    settings = get_settings()
    engine = create_engine(settings.TEST_DATABASE_URL)
    session_factory = sessionmaker(bind=engine)

    import uuid

    run_id = str(uuid.uuid4())
    test_pdf_path = tmp_path / f"test_bio_grade12_{run_id}.pdf"
    p1 = f"Run {run_id}. Chapter 1: Applications of Biology. Modern biotechnology has transformed agriculture and medicine. " * 10
    p2 = "Enzymes play a pivotal role as biological catalysts in cellular respiration. Cell metabolism requires ATP. " * 10
    p3 = "Chapter 2: Microorganisms. Bacteria and viruses have distinct structures and modes of replication. " * 10
    create_sample_pdf(test_pdf_path, [p1, p2, p3])

    manifest = [
        {
            "number": 1,
            "title_en": "Applications of Biology",
            "title_am": "የስነ-ህይወት አተገባበር",
            "first_page": 1,
            "last_page": 2,
        },
        {
            "number": 2,
            "title_en": "Microorganisms",
            "title_am": "ደቂቅ አካላት",
            "first_page": 3,
            "last_page": 3,
        },
    ]

    embedder = FakeEmbedder()

    # 2. Ingest first time
    with session_factory() as session:
        doc1, skipped1 = ingest_textbook(
            db=session,
            pdf_path=test_pdf_path,
            grade_id=12,
            subject_id="biology",
            title="Grade 12 Biology Test Book",
            edition="2026",
            chapters_manifest=manifest,
            embedder=embedder,
        )

        assert skipped1 is False
        assert doc1.status == "ready"
        assert doc1.page_count == 3
        doc1_id = doc1.id

        # Verify pages saved
        pages = session.query(Page).filter(Page.document_id == doc1_id).all()
        assert len(pages) == 3

        # Verify chunks created with 1024-dim embeddings and correct chapter mappings
        chunks = session.query(Chunk).filter(Chunk.document_id == doc1_id).all()
        assert len(chunks) >= 3
        for chunk in chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 1024
            assert chunk.page_no in (1, 2, 3)

        # Check chapter linkage
        p1_chunk = next(c for c in chunks if c.page_no == 1)
        p3_chunk = next(c for c in chunks if c.page_no == 3)
        ch1 = session.query(Chapter).filter(Chapter.book_id == doc1.book_id, Chapter.number == 1).first()
        ch2 = session.query(Chapter).filter(Chapter.book_id == doc1.book_id, Chapter.number == 2).first()
        assert p1_chunk.chapter_id == ch1.id
        assert p3_chunk.chapter_id == ch2.id

    # 3. Ingest second time with same PDF -> must be skipped by text_hash
    with session_factory() as session:
        doc2, skipped2 = ingest_textbook(
            db=session,
            pdf_path=test_pdf_path,
            grade_id=12,
            subject_id="biology",
            title="Grade 12 Biology Test Book",
            edition="2026",
            chapters_manifest=manifest,
            embedder=embedder,
        )

        assert skipped2 is True
        assert doc2.id == doc1_id
