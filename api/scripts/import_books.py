"""Import textbook PDFs into the Tibeb library with per-page chunking and embeddings.

Usage:
    python scripts/import_books.py <path_to_pdf> --grade 12 --subject biology [--edition 2026] [--chapters <path_to_yaml>]
"""

import argparse
from pathlib import Path

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.providers.registry import get_embedder
from app.services.ingestion import (
    ScannedPDFError,
    chunk_document_pages,
    extract_pages_from_pdf,
    ingest_textbook,
)


def load_chapters_yaml(yaml_path: Path) -> tuple[dict, list[dict]]:
    """Load book metadata and chapter page ranges from a YAML manifest."""
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    book_meta = data.get("book", {})
    chapters = data.get("chapters", [])
    return book_meta, chapters


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest Ethiopian national curriculum textbook PDFs into library."
    )
    parser.add_argument("pdf", type=str, help="Path to textbook PDF file")
    parser.add_argument("--grade", type=int, help="Grade number (e.g. 9, 10, 11, 12)")
    parser.add_argument("--subject", type=str, help="Subject code (e.g. biology, chemistry, physics)")
    parser.add_argument("--edition", type=str, default="2026", help="Book edition (default: 2026)")
    parser.add_argument("--title", type=str, default=None, help="Book title override")
    parser.add_argument("--chapters", type=str, default=None, help="Path to chapter ranges YAML file")
    parser.add_argument("--test-db", action="store_true", help="Ingest into TEST_DATABASE_URL")
    parser.add_argument("--db-url", type=str, default=None, help="Explicit database URL")
    parser.add_argument("--dry-run", action="store_true", help="Extract and chunk without database writing")
    parser.add_argument("--force", action="store_true", help="Force re-ingest even if text hash exists")

    args = parser.parse_args()
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return

    # Check for accompanying YAML manifest if not explicitly given
    chapters_path = None
    if args.chapters:
        chapters_path = Path(args.chapters)
    else:
        sibling_yaml = pdf_path.with_suffix(".yaml")
        if sibling_yaml.exists():
            chapters_path = sibling_yaml

    chapters_manifest: list[dict] = []
    book_meta: dict = {}
    if chapters_path and chapters_path.exists():
        print(f"Loading chapter manifest from {chapters_path}...")
        book_meta, chapters_manifest = load_chapters_yaml(chapters_path)

    grade = args.grade or book_meta.get("grade")
    subject = args.subject or book_meta.get("subject")
    edition = args.edition or book_meta.get("edition", "2026")

    if not grade or not subject:
        print("Error: --grade and --subject must be specified (or defined in chapter YAML).")
        return

    title = args.title or book_meta.get("title") or f"Grade {grade} {subject.title()} Student Textbook"

    print(f"\n--- Ingesting Textbook: {title} ---")
    print(f"PDF: {pdf_path}")
    print(f"Grade: {grade} | Subject: {subject} | Edition: {edition}")
    print(f"Chapters declared: {len(chapters_manifest)}")

    # 1. Extract pages & detect scanned PDFs
    try:
        pages = extract_pages_from_pdf(pdf_path)
    except ScannedPDFError as e:
        print(f"\n[REJECTED] {e}")
        return
    except Exception as e:  # noqa: BLE001
        print(f"\n[ERROR] Failed to extract PDF text: {e}")
        return

    total_chars = sum(p.char_count for p in pages)
    print(f"Extracted {len(pages)} pages ({total_chars:,} total characters).")

    # 2. Chunking preview
    chunks = chunk_document_pages(pages)
    print(f"Created {len(chunks)} page-scoped chunks (never crossing pages).")

    if args.dry_run:
        print("\n[DRY RUN COMPLETE] No database changes made.")
        return

    # 3. Database connection
    settings = get_settings()
    if args.db_url:
        db_url = args.db_url
    elif args.test_db:
        db_url = settings.TEST_DATABASE_URL
    else:
        db_url = settings.DATABASE_URL

    engine = create_engine(db_url)
    session_factory = sessionmaker(bind=engine)
    embedder = get_embedder(settings)

    print(f"\nConnecting to database ({db_url.split('@')[-1] if '@' in db_url else db_url})...")
    with session_factory() as session:
        doc, skipped = ingest_textbook(
            db=session,
            pdf_path=pdf_path,
            grade_id=grade,
            subject_id=subject,
            title=title,
            edition=edition,
            chapters_manifest=chapters_manifest,
            embedder=embedder,
            force=args.force,
        )

        if skipped:
            print(f"[SKIPPED] Book text hash {doc.text_hash[:16]}... already exists in documents (id={doc.id}).")
        else:
            print(f"[SUCCESS] Ingested document id={doc.id} with status={doc.status} ({len(chunks)} chunks saved).")


if __name__ == "__main__":
    main()
