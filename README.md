# Tibeb AI — Amharic AI Study Tutor

An AI-powered study tutor for Ethiopian high-school students, explaining national-curriculum textbooks and personal study notes in Amharic and English via text and voice, with exam practice and offline support.

## Project Structure

```text
/
├─ docs/                  # Architecture, Playbook (with Build log), Decisions
├─ api/                   # FastAPI backend server + RQ background worker
│  ├─ app/                # Main application, routes, providers, services, db, prompts
│  ├─ worker/             # Background ingestion and flashcard generation jobs
│  ├─ scripts/            # CLI utilities: import books, seed testers, smoke check
│  ├─ tests/              # Automated tests (pytest)
│  └─ config/             # Environment & provider YAML configurations
├─ mobile/                # Flutter mobile application (Android priority)
├─ admin/                 # Next.js admin portal (Phase 4)
├─ docker-compose.yml     # Redis and pgvector test database services
├─ Makefile               # Unified development commands
└─ .gitignore
```

## Getting Started

### Prerequisites

- Git
- Docker Desktop (running)
- Python 3.12 (managed via `uv`)
- `uv` (Fast Python package manager)
- Flutter SDK (stable channel) with Android toolchain
- Node.js LTS
- GNU Make

### Quick Commands

```bash
# Run all automated tests (uses fake providers, no paid/external API calls)
make test

# Start local redis & test-db containers, and launch FastAPI dev server
make dev

# Run database migrations
make migrate

# Seed database
make seed

# Run Amharic model quality evaluations (explicit, uses configured providers)
make eval

# Smoke test external provider connections
make smoke

# Stop background docker services
make down
```

### Mobile App (Flutter)

```bash
cd mobile
flutter test
flutter run
```
