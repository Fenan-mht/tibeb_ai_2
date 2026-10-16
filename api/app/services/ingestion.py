"""Library and textbook ingestion service.

Extracts text per page using PyMuPDF, detects scanned PDFs, cleans text,
splits into page-scoped chunks (400-600 tokens, ~15% overlap, NEVER across pages),
computes text hash for deduplication, and generates 1024-dimensional embeddings.
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import fitz  # PyMuPDF
from sqlalchemy.orm import Session

from app.db.models import Book, Chapter, Chunk, Document, Page
from app.providers.base import Embedder


class IngestionError(Exception):
    """Base exception for document ingestion errors."""


class ScannedPDFError(IngestionError):
    """Raised when a PDF has too many image-only or low-text pages."""


@dataclass
class ExtractedPage:
    page_no: int
    text: str
    char_count: int


@dataclass
class TextChunk:
    text: str
    page_no: int
    token_count: int


def estimate_tokens(text: str) -> int:
    """Estimate token count for mixed Amharic/English text (~4 characters per token)."""
    # Uses max of word-count heuristic (1.3 tokens/word) and character heuristic (chars/4)
    words = text.split()
    word_tokens = int(len(words) * 1.3)
    char_tokens = max(1, len(text) // 4)
    return max(word_tokens, char_tokens)


def clean_text(text: str) -> str:
    """Clean extracted page text: normalize whitespace, fix broken hyphenation, strip noise."""
    if not text:
        return ""

    # Fix broken hyphenation across line breaks (e.g. 'bio-\nlogy' -> 'biology')
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    # Normalize standalone line breaks within paragraphs to spaces
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Collapse multiple consecutive blank lines into double newline
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Collapse repeated whitespace
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def extract_pages_from_pdf(
    pdf_source: str | Path | BinaryIO | bytes,
    max_page_chars: int = 6000,
    scanned_threshold: float = 0.30,
    min_chars_per_page: int = 50,
) -> list[ExtractedPage]:
    """Extract and clean text per page from a PDF file.

    Enforces scanned-page rejection: if >30% of pages have fewer than 50 characters,
    raises ScannedPDFError.
    """
    if isinstance(pdf_source, (str, Path)):
        doc = fitz.open(str(pdf_source))
    elif isinstance(pdf_source, bytes):
        doc = fitz.open(stream=pdf_source, filetype="pdf")
    else:
        # File-like object
        stream = pdf_source.read()
        doc = fitz.open(stream=stream, filetype="pdf")

    total_pages = len(doc)
    if total_pages == 0:
        raise IngestionError("PDF contains no pages.")

    pages: list[ExtractedPage] = []
    short_pages_count = 0

    for i in range(total_pages):
        page = doc[i]
        page_no = i + 1  # 1-indexed
        raw_text = page.get_text()
        cleaned = clean_text(raw_text)

        # Truncate if exceeds page cap
        if len(cleaned) > max_page_chars:
            cleaned = cleaned[:max_page_chars]

        if len(cleaned) < min_chars_per_page:
            short_pages_count += 1

        pages.append(ExtractedPage(page_no=page_no, text=cleaned, char_count=len(cleaned)))

    doc.close()

    # Scanned PDF check
    short_ratio = short_pages_count / total_pages
    if short_ratio > scanned_threshold:
        raise ScannedPDFError(
            f"Scanned PDF detected: {short_pages_count} of {total_pages} pages ({short_ratio:.1%}) "
            f"have fewer than {min_chars_per_page} characters. Scanned image PDFs are not supported."
        )

    return pages


def compute_text_hash(pages: list[ExtractedPage]) -> str:
    """Compute deterministic SHA-256 hash of all extracted page texts."""
    hasher = hashlib.sha256()
    for p in pages:
        hasher.update(f"---PAGE {p.page_no}---\n{p.text}\n".encode())
    return hasher.hexdigest()


def chunk_page_text(
    page_text: str,
    page_no: int,
    min_tokens: int = 400,
    max_tokens: int = 600,
    overlap_ratio: float = 0.15,
) -> list[TextChunk]:
    """Split text of a single page into chunks of 400-600 tokens with ~15% overlap.

    CRITICAL RULE: Chunking never crosses page boundaries. Every chunk produced
    belongs strictly to `page_no`.
    """
    if not page_text or not page_text.strip():
        return []

    # If the entire page fits within the maximum token cap, return as a single chunk
    total_tokens = estimate_tokens(page_text)
    if total_tokens <= max_tokens:
        return [TextChunk(text=page_text, page_no=page_no, token_count=total_tokens)]

    # Split page into sentences / paragraph fragments for natural boundaries
    # Supports both Latin punctuation (. ! ?) and Ethiopic punctuation (። ፧ ፨)
    sentences = re.split(r"(?<=[.!?።፧፨\n])\s+", page_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks: list[TextChunk] = []
    current_sentences: list[str] = []
    current_tokens = 0
    overlap_tokens_target = int(min_tokens * overlap_ratio)

    for sentence in sentences:
        s_tokens = estimate_tokens(sentence)

        if current_tokens + s_tokens > max_tokens and current_tokens >= min_tokens:
            # Emit current chunk
            chunk_text = " ".join(current_sentences)
            chunks.append(
                TextChunk(text=chunk_text, page_no=page_no, token_count=current_tokens)
            )

            # Build overlap from trailing sentences
            overlap_sentences: list[str] = []
            overlap_count = 0
            for prev_s in reversed(current_sentences):
                prev_tokens = estimate_tokens(prev_s)
                if overlap_count + prev_tokens <= overlap_tokens_target:
                    overlap_sentences.insert(0, prev_s)
                    overlap_count += prev_tokens
                else:
                    break

            current_sentences = overlap_sentences + [sentence]
            current_tokens = overlap_count + s_tokens
        else:
            current_sentences.append(sentence)
            current_tokens += s_tokens

    if current_sentences:
        chunk_text = " ".join(current_sentences)
        chunks.append(
            TextChunk(text=chunk_text, page_no=page_no, token_count=current_tokens)
        )

    return chunks


def chunk_document_pages(
    pages: list[ExtractedPage],
    min_tokens: int = 400,
    max_tokens: int = 600,
) -> list[TextChunk]:
    """Chunk all pages, strictly keeping chunks within individual page boundaries."""
    all_chunks: list[TextChunk] = []
    for page in pages:
        page_chunks = chunk_page_text(
            page.text,
            page_no=page.page_no,
            min_tokens=min_tokens,
            max_tokens=max_tokens,
        )
        all_chunks.extend(page_chunks)
    return all_chunks


def ingest_textbook(
    db: Session,
    pdf_path: str | Path,
    grade_id: int,
    subject_id: str,
    title: str,
    edition: str = "2026",
    chapters_manifest: list[dict] | None = None,
    embedder: Embedder | None = None,
    force: bool = False,
) -> tuple[Document, bool]:
    """Ingest a textbook PDF into the database.

    Returns:
        (Document, was_skipped)
    """
    # 1. Extract text and detect scanned PDFs
    pages = extract_pages_from_pdf(pdf_path)
    text_hash = compute_text_hash(pages)

    # 2. Check for duplicate ingestion by text_hash
    existing_doc = (
        db.query(Document)
        .filter(Document.text_hash == text_hash, Document.owner_type == "library")
        .first()
    )
    if existing_doc and not force:
        return existing_doc, True  # Skipped by hash

    # 3. Find or create Book
    book = (
        db.query(Book)
        .filter(
            Book.grade_id == grade_id,
            Book.subject_id == subject_id,
            Book.edition == edition,
        )
        .first()
    )
    if not book:
        book = Book(
            grade_id=grade_id,
            subject_id=subject_id,
            title=title,
            edition=edition,
            status="active",
            source="moe",
        )
        db.add(book)
        db.flush()

    # 4. Upsert chapters from manifest if provided
    chapter_objs: dict[int, Chapter] = {}
    if chapters_manifest:
        for ch_data in chapters_manifest:
            ch_num = ch_data["number"]
            ch = (
                db.query(Chapter)
                .filter(Chapter.book_id == book.id, Chapter.number == ch_num)
                .first()
            )
            if not ch:
                ch = Chapter(
                    book_id=book.id,
                    number=ch_num,
                    title_en=ch_data["title_en"],
                    title_am=ch_data.get("title_am", ch_data["title_en"]),
                    first_page=ch_data["first_page"],
                    last_page=ch_data["last_page"],
                )
                db.add(ch)
                db.flush()
            else:
                ch.title_en = ch_data["title_en"]
                ch.title_am = ch_data.get("title_am", ch_data["title_en"])
                ch.first_page = ch_data["first_page"]
                ch.last_page = ch_data["last_page"]

            chapter_objs[ch_num] = ch

    # 5. Create Document record
    document = Document(
        owner_type="library",
        book_id=book.id,
        title=title,
        page_count=len(pages),
        text_hash=text_hash,
        status="processing",
    )
    db.add(document)
    db.flush()

    # 6. Save raw pages
    for p in pages:
        db_page = Page(
            document_id=document.id,
            page_no=p.page_no,
            text=p.text,
        )
        db.add(db_page)

    # 7. Chunk all pages (strictly page-scoped)
    chunks = chunk_document_pages(pages)

    # 8. Generate embeddings
    chunk_texts = [c.text for c in chunks]
    embeddings: list[list[float]] = []
    if embedder and chunk_texts:
        vectors, _usage = embedder.embed(chunk_texts)
        embeddings = vectors
    else:
        # If no embedder provided, assign None
        embeddings = [None] * len(chunks)

    # 9. Map chunks to chapters and persist
    for idx, c in enumerate(chunks):
        # Determine chapter by page_no
        matched_chapter_id = None
        for ch in chapter_objs.values():
            if ch.first_page <= c.page_no <= ch.last_page:
                matched_chapter_id = ch.id
                break

        db_chunk = Chunk(
            document_id=document.id,
            chapter_id=matched_chapter_id,
            page_no=c.page_no,
            text=c.text,
            token_count=c.token_count,
            embedding=embeddings[idx],
        )
        db.add(db_chunk)

    document.status = "ready"
    db.commit()

    return document, False
