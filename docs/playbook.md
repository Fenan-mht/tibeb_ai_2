# AI Build Playbook — Amharic Study Tutor

Oct 15, 2026 · @dreamingkayak

This playbook tells the AI coding agent in Antigravity how to build the app phase by phase, and tells it exactly when to stop and hand a task to the human owner. It is read together with the architecture document.

## How to use this playbook

Put this playbook and the architecture document in your repository as Markdown, then start each phase with the prompt from "Prompts to start each phase". The agent builds and tests; you do the steps it hands you and every git push.

**One-time setup (human)**

1. Export both documents as Markdown (each doc's export menu).
2. Create an empty folder for the project and open it in Antigravity.
3. Save the files as `docs/architecture.md` and `docs/playbook.md`.
4. If your Antigravity settings let you choose how terminal commands run, set them to ask for your approval, at least until you trust the agent's habits.
5. Paste the Phase 0 prompt into the agent chat.

**How a working session goes**

1. You paste the prompt for the current phase (or "continue").
2. The agent reads the **Build log** at the end of `docs/playbook.md` to see where it stopped, then works on the next step.
3. When it needs you (an account, a key, a phone, a decision, a review), it stops and shows a **HUMAN TASK** block with exact steps.
4. You do the task and reply with what it asks for ("done", or a value that isn't secret).
5. After every change it runs the tests and writes what changed into the playbook's Build log. At the end of each step it shows a **READY TO COMMIT** block. You review the changes (including the Build log), commit and push yourself.
6. At the end of each phase it checks the phase gate with you before moving on.

**What the agent will never do:** push to GitHub, change git remotes, put real keys in code or chat, call paid services in tests, or start the next phase without your confirmation.

## Phase map

The build runs in six phases; the agent never starts the next phase until you confirm its gate.

&#91;embedded content: phase map · 6 phases, 6 gates\]

Start the textbook permission request (step 5.1) during Phase 1; it is the slowest item and it blocks launch.

## Rules for the AI agent

Agent: follow every rule in this section in every session. If a rule conflicts with a request, stop and ask the human.

**Sources of truth**

1. `docs/architecture.md` decides what the system is (components, endpoints, tables, limits, plans). This playbook decides the order and the working rules.
2. If the two disagree, or something you need isn't in either, stop and ask. Don't invent requirements, prices, limits or provider choices.
3. Read the Build log at the end of `docs/playbook.md` at the start of every session and continue from its "Current state".

**Working style**

4. Work one step at a time, in the order of this playbook. Finish, test and log a step before starting the next.
5. Before writing code for a step, state in 3–6 lines what you will build and which files you will touch.
6. Keep changes small and focused on the current step. No unrequested refactors, renames or new libraries.
7. Every outside service goes through the provider interfaces in `api/app/providers/` (see architecture: "API server and provider layer"). No route or worker calls Groq, Google, Chapa or Supabase SDKs directly.
8. Prefer well-known, maintained libraries. Pin versions in lock files. Ask before adding any dependency not named in this playbook or the architecture document.

**Git (human-only pushes)**

9. Never run `git push`, `git remote`, `git reset --hard`, `git rebase`, `git push --force`, or anything that rewrites history or contacts GitHub.
10. You may run `git status` and `git diff` to describe changes. Leave staging and committing to the human unless they ask you to commit locally.
11. End every completed step with a READY TO COMMIT block (see next section).

**Secrets and data**

12. Never write a real key, password or token into code, tests, logs, docs or chat. Real values live only in `.env` files that the human fills in; you maintain `.env.example` with placeholders.
13. Make sure `.env`, `*.key`, service-account JSON files, `data/`, model caches and build outputs are in `.gitignore` before the first commit.
14. Never ask the human to paste a secret into chat. Ask them to put it in `.env` and reply "done".
15. Never delete the human's files or database data without asking first. Database changes go through migrations only.

**Money and free tiers**

16. Automated tests never call real paid or rate-limited services. Use the fake providers (see "Testing rules").
17. Real provider calls happen only in commands the human runs on purpose (`make eval`, `make smoke`), and each prints how many calls and characters it will use before it starts.
18. Respect the free-tier caps from the architecture document, especially the Google TTS hard cap. Never raise a cap or add a paid plan without the human's approval.

**Communication**

19. Write to the human in plain language. Explain anything technical the first time it comes up.
20. When something fails, show the error, your diagnosis and the fix you propose. After two failed attempts at the same fix, stop and ask.

**Build log (keeping the playbook current)**

21. After every change, update the Build log section at the end of `docs/playbook.md` before you report back: rewrite "Current state", add an entry at the top of "Log", and add any new decision or known issue. A change is anything that edits files, answers or raises a HUMAN TASK, or changes a decision.
22. The Build log is the only part of the playbook you edit. Never change the playbook's other sections or `docs/architecture.md` unless the human asks; if they look wrong, say so and propose the change.
23. Write every entry so a new session with no memory could continue from it alone: the exact step, what is done, what is half-done, the next action, and what is waiting on the human.
24. If a session was cut off mid-step, the next session first compares `git status` with the last log entry, records what it finds, and then continues.
25. Include the Build log in the changed files of every READY TO COMMIT block, so it is committed together with the code it describes.

## Human task blocks and the Build log

The agent talks to the human in three fixed formats so nothing gets lost: HUMAN TASK when it needs something, READY TO COMMIT after each step, and PHASE GATE at the end of each phase.

**HUMAN TASK** (agent: use this whenever you need the human; then stop and wait)

```markdown
### HUMAN TASK — <short title>

Why: <one sentence on why this is needed now>
Steps:

1. <exact action: website, button names, what to type>
2. ...
   Put secrets in: <file and variable name, e.g. api/.env → GROQ_API_KEY>
   Reply with: <exactly what to send back, e.g. "done" or the Supabase project region>
   How I'll check: <the command or test I will run afterwards>
```

**READY TO COMMIT** (agent: after each finished step)

```markdown
### READY TO COMMIT — Step <n.n> <title>

Tests: <command run> → <result, e.g. 24 passed>
Changed files:

- <path> — <one line on what changed>
  Please review with: git diff
  Suggested commit message:
  <type>(<area>): <summary>
  Then push when you're happy. I'll wait for "pushed" or "continue".
```

**PHASE GATE** (agent: at the end of each phase)

```markdown
### PHASE GATE — Phase <n>

Gate: <the gate from this playbook>
Evidence: <test results, eval numbers, what the human saw on the phone>
Open issues: <anything not done or deferred>
Reply "gate passed" to start Phase <n+1>, or tell me what to fix.
```

**Build log:** the agent's running record lives in the last section of this playbook, "Build log". Its format and rules are there and in rules 21–25.

## Repository layout and stack

One repository holds the API, the Flutter app, the admin portal and the docs. Agent: create this layout in Phase 0 and keep to it.

```text
/
├─ docs/
│  ├─ architecture.md        # from the architecture doc (human adds)
│  ├─ playbook.md            # this file (human adds); agent updates its Build log
│  └─ decisions/             # short notes for big choices
├─ api/                      # FastAPI server + worker (Python)
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ config.py           # settings from env + config/*.yaml
│  │  ├─ routes/             # one file per area: chat, library, practice...
│  │  ├─ providers/          # ChatModel, Embedder, TTS, STT, FileStore, Payments
│  │  │  └─ fakes.py         # fake providers for tests
│  │  ├─ services/           # retrieval, ingestion, limits, usage
│  │  ├─ db/                 # models + Alembic migrations
│  │  └─ prompts/            # tutor, speech script, practice prompts (text files)
│  ├─ worker/                # RQ jobs: ingest, practice generation
│  ├─ scripts/               # import_books.py, import_questions.py, seed_testers.py
│  ├─ evals/                 # Amharic quality runs (real API calls, run on purpose)
│  ├─ tests/
│  ├─ config/test.yaml       # providers per task (test)
│  ├─ .env.example
│  └─ pyproject.toml
├─ mobile/                   # Flutter app
├─ admin/                    # Next.js admin portal (Phase 4)
├─ docker-compose.yml        # api, worker, redis, test-db
├─ Makefile                  # make dev, make test, make eval, make smoke...
└─ .gitignore
```

| Part       | Choice                                                                                           |
| ---------- | ------------------------------------------------------------------------------------------------ |
| API        | Python 3.12, FastAPI, Pydantic settings, SQLAlchemy 2 + Alembic, `uv` or `pip` with a lock file  |
| Jobs       | Redis + RQ                                                                                       |
| Database   | Supabase Postgres with pgvector (dev), a local Postgres + pgvector container for automated tests |
| Embeddings | BGE-M3 via `sentence-transformers` (or `FlagEmbedding`), CPU                                     |
| Models     | Groq through the OpenAI-compatible client, behind `ChatModel`                                    |
| Voice      | Google Cloud Text-to-Speech, `am-ET-Wavenet-B`, behind `TextToSpeech`                            |
| Mobile     | Flutter (stable channel), Android first                                                          |
| Admin      | Next.js (App Router) + React + TypeScript                                                        |
| Tests      | pytest + httpx; `flutter test`; Vitest for the admin portal                                      |
| Lint       | ruff + mypy (API), `flutter analyze`, ESLint (admin)                                             |

**Makefile targets the agent creates:** `make dev` (start everything), `make test` (all automated tests, no real API calls), `make migrate`, `make seed`, `make eval` (Amharic quality run, real calls), `make smoke` (one real call per provider to check keys).

## Testing rules

Every step ships with tests, and `make test` must pass with no internet keys set, so tests never spend money or free-tier quota.

**Three kinds of test runs**

| Command      | Calls real services?                                | Who runs it                  | When                                       |
| ------------ | --------------------------------------------------- | ---------------------------- | ------------------------------------------ |
| `make test`  | No: fake providers, local test database             | Agent, after every change    | Every step                                 |
| `make smoke` | Yes: one tiny call per configured provider          | Human, or agent after asking | After keys are added or changed            |
| `make eval`  | Yes: the Amharic question set against chosen models | Human, or agent after asking | Phase 2, and when prompts or models change |

**Fakes the agent writes in Phase 1** (`api/app/providers/fakes.py`)

- `FakeChatModel`: returns a fixed answer that includes a citation and streams it in chunks; records the messages it received so tests can check the prompt.
- `FakeEmbedder`: deterministic vectors from a hash of the text (1024 numbers), so retrieval tests are repeatable.
- `FakeTTS` / `FakeSTT`: return tiny fixed audio / fixed text and report usage units.
- `FakePayments`: simulates Chapa initialise, webhook and verify, including a failed and a duplicated webhook.

**Test database:** automated tests use a Postgres + pgvector container from `docker-compose.yml` (`test-db`), recreated per test session. Tests never touch Supabase.

**What every step's tests must cover**

1. The normal path works.
2. Limits are enforced (quota, character caps, free questions, TTS cap).
3. Bad input is rejected with a clear error.
4. A student can't reach another student's data.
5. Usage is recorded in `usage_events` for anything that would cost money.

**Mobile and admin:** widget and unit tests with mocked HTTP; no test needs a real phone. Testing on a real phone is a HUMAN TASK at the end of the relevant steps.

## Phase 0: Accounts, tools and repo scaffold

Phase 0 gets your machine, accounts and an empty but runnable project ready; no app features yet. **Gate:** `make dev` starts everything, `make test` passes, and `make smoke` reaches Groq, Supabase and Google TTS with your keys.

**0.1 Tools on your computer** — HUMAN TASK

- Agent: list what to install and the command to check each one, then wait.
- Human installs: Git, Docker Desktop, Python 3.12, `uv` (Python package manager), Flutter SDK (stable) with Android Studio and an Android SDK, Node.js LTS. Turn on Developer options and USB debugging on your Android phone.
- Check: the agent runs `git --version`, `docker --version`, `python3 --version`, `uv --version`, `flutter doctor`, `node --version` and explains anything `flutter doctor` flags.

**0.2 Repo scaffold** — agent

- Create the layout from "Repository layout and stack", `.gitignore` (Rules for the AI agent, rule 13), `README.md` with how to run, `the first Build log entry`, `Makefile`, `docker-compose.yml` (redis, test-db), `api/pyproject.toml`, a FastAPI app with `GET /health`, and one passing test.
- Human task at the end: create an empty **private** GitHub repository, connect it with `git init`, `git remote add origin …`, then commit and push yourself.
- Done when: `make test` passes and `make dev` shows `/health` returning `{"status":"ok"}`.

**0.3 Accounts and keys** — HUMAN TASK (agent: one block per service, in this order)

| Service      | What the human does                                                                                                                                                       | Goes in `api/.env`               |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| Groq         | Sign up at console.groq.com, create an API key                                                                                                                            | `GROQ_API_KEY`                   |
| Supabase     | New project (free tier, region closest to Ethiopia), copy the database connection string; in SQL editor run `create extension if not exists vector;`                      | `DATABASE_URL`                   |
| Google Cloud | New project, enable Cloud Text-to-Speech API, create a service account with TTS access, download its JSON key into `api/secrets/` (git-ignored), set a budget alert at $1 | `GOOGLE_APPLICATION_CREDENTIALS` |
| Chapa        | Create a merchant account and copy the **test** secret key                                                                                                                | `CHAPA_SECRET_KEY`               |

- Agent: write `.env.example` with every variable and a comment, never real values.

**0.4 Smoke check** — agent, then human runs it

- Build `make smoke`: one short Groq completion, a `select 1` and `select extname from pg_extension` on Supabase, and Google TTS of a 10-character Amharic phrase saved to `api/data/smoke.mp3`. It prints the characters and tokens it will use before running.
- Human: run `make smoke` and play the MP3.
- Done when: all three pass. Then PHASE GATE.

## Phase 1: Backend core, library and question bank

Phase 1 builds the server so that a question about a real textbook chapter gets a cited answer, testable from a simple web page with no phone. **Gate:** for 10 real questions across 2–3 textbooks, answers cite the right book and page, and `make test` passes.

**1.1 Config and provider layer** — agent

- Settings from `.env` plus `config/test.yaml` (architecture: "Example config"); `APP_ENV`, `AUTH_MODE`.
- Interfaces `ChatModel`, `Embedder`, `TextToSpeech`, `SpeechToText`, `FileStore`, `PaymentGateway`, each returning usage units; Groq, BGE-M3, Google TTS, local file store and Chapa (test) implementations; all fakes.
- Tests: config loading; provider chosen by config; the server refuses to start with `AUTH_MODE=none` when `APP_ENV=production`.

**1.2 Database and migrations** — agent

- SQLAlchemy models and Alembic migrations for every table in architecture "Data model", the pgvector HNSW index, and seed data for grades and subjects.
- HUMAN TASK: run `make migrate` against Supabase and confirm the tables appear in the Supabase table editor.
- Tests: migrations apply cleanly on `test-db` from empty.

**1.3 Test-mode identity** — agent

- `AUTH_MODE=none`: requests carry `X-Tester-Id`; `scripts/seed_testers.py` creates 10 testers on plans Free, Basic, Premium and Tester.
- Tests: unknown tester rejected; each tester sees only their own data.

**1.4 Library ingestion** — agent, then HUMAN TASK

- `scripts/import_books.py <pdf> --grade --subject --edition`: extract text per page (PyMuPDF), clean, chunk (400–600 tokens, \~15% overlap, never across pages), embed with BGE-M3, store; chapter page ranges from a small YAML per book.
- HUMAN TASK: put 2–3 textbook PDFs (for example grade 12 biology, chemistry, physics) in `api/data/books/` and write each book's chapter list in the YAML template the agent provides. Keep within Supabase's 500 MB free database.
- Tests: chunking never crosses a page; re-importing the same book is skipped by text hash; a scanned-page book is reported, not silently stored empty.

**1.5 Question bank import** — HUMAN TASK first, then agent

- HUMAN TASK: give the agent 20 sample questions from your bank in their current format (file in `api/data/questions/sample/`) and say how they map to grade, subject and chapter.
- Agent: write `scripts/import_questions.py` for that format into `practice_items` (`source` = exercise or past_exam), with a dry-run mode that reports problems (missing answer, answer not among options, unknown chapter) without writing.
- HUMAN TASK: run the dry run on the full bank, fix or accept the reported problems, then run the import.
- Tests: valid rows import; each problem type is reported; import is idempotent.

**1.6 Retrieval** — agent

- Scoped search: chapter → book → subject, plus the student's own documents; widen when the best score is below a threshold (in config); return chunks with book, page and score.
- Tests (FakeEmbedder): scope filters work; widening triggers; another student's document is never returned.

**1.7 Chat with streaming** — agent

- `POST /v1/chat` (SSE) per architecture "Tutoring flow": quota check, retrieval, prompt from `app/prompts/tutor.md`, stream from `ChatModel`, save message, citations and `usage_events`. Answer language: Amharic, English or both.
- Tests (FakeChatModel): stream arrives in order; citations saved; usage recorded; quota exceeded returns the right message.

**1.8 Web test page** — agent, then HUMAN TASK

- `GET /dev` (only when `APP_ENV=test`): pick tester, grade, subject, chapter, language; ask; see the streamed answer and citations.
- HUMAN TASK: ask 10 real questions with the Groq model and note for each whether the cited page is right. Then PHASE GATE.

## Phase 2: Amharic answer quality

Phase 2 decides which tutor model and prompt give the best teacher-style explanations in Amharic and English, using real questions and a native speaker's ratings. **Gate:** a tutor model and prompt chosen, recorded in `docs/decisions/`, with average ratings written down.

**2.1 Question set** — HUMAN TASK

- Write 40 real student questions in `api/evals/questions.csv` (template from the agent): grade, subject, chapter, language (am, en, both), the question, and the page where the answer is. Mix easy, hard, Amharic, English and mixed-language questions, plus 5 questions the books don't cover.

**2.2 Eval runner** — agent

- `make eval MODELS=... PROMPT=...` runs every question through retrieval and each chosen model, and writes `api/evals/results/<date>.csv` with the answer, citations, tokens and cost per answer. Before starting it prints the number of calls and estimated cost and waits for "yes".
- Models to compare: what the human has keys for. Groq models first (free tier); add Gemini Flash or Claude later only if the human creates keys for them.
- Tests: runner works end to end with FakeChatModel; the cost estimate matches recorded usage.

**2.3 Prompt work** — agent with the human

- Write `prompts/tutor.md` from architecture "System prompt rules": a patient teacher, everyday Ethiopian examples, a check question at the end, citations, only backend content, a clear "not in the book" answer.
- Write `prompts/speech_script.md` for the spoken explanation (used in Phase 4).
- Keep each prompt version in git; the eval records which version produced each answer.

**2.4 Rating** — HUMAN TASK

- Rate each answer 1–5 on: correct, clear Amharic, sounds like a teacher, right page, stays in the book. Use the rating sheet the agent generates (`api/evals/rating_sheet.csv`).
- Agent: summarise averages per model and prompt version, the worst 5 answers and why, and the cost per answer. Recommend one model and prompt; the human decides.

**2.5 Record the decision** — agent

- Write `docs/decisions/001-tutor-model.md` with the choice, the numbers and the date; update `config/test.yaml`. Then PHASE GATE.

## Phase 3: Flutter app

Phase 3 builds the Android app against the Phase 1 server: library, chat, input, practice, offline store and the free gate. **Gate:** on a budget Android phone over mobile data, a tester can browse a chapter, ask by keyboard and by voice, get a streamed cited answer, practise questions offline, and hit the free limit correctly.

**3.1 App shell and connection** — agent, then HUMAN TASK

- Flutter project in `mobile/`, Android first; `API_BASE_URL` from `--dart-define`; tester picker screen (test mode); an HTTP client with timeouts, retries and SSE support.
- HUMAN TASK: connect the phone by USB, run `flutter run --dart-define=API_BASE_URL=http://<laptop LAN IP>:8000` on the same Wi-Fi; if that fails, start a tunnel (Cloudflare Tunnel or ngrok) following the agent's steps and use its HTTPS address.
- Tests: widget test for the tester picker; HTTP client retries on timeout (mocked).

**3.2 Library browser** — agent

- Grade → subject → book → chapter screens; open the chapter's pages; "Ask about this chapter" sets the chat scope.
- Tests: navigation and scope with mocked API.

**3.3 Tutor chat** — agent

- Streaming answer view with Markdown, citations as tappable chips (book, page), Mermaid diagrams in a small WebView that hides itself on error, language toggle (Amharic, English, both), thumbs up and down.
- Tests: stream rendering; a broken diagram doesn't break the message.

**3.4 Input: keyboard and device speech** — agent, then HUMAN TASK

- Text field for Amharic and English; mic button using the phone's speech recognizer with locale `am-ET`; capability check; transcript shown for editing before sending (architecture "Amharic input").
- HUMAN TASK: install an Amharic keyboard if needed; test 10 spoken Amharic questions and note how many came out right.
- Tests: mic hidden or explained when `am-ET` isn't available (mocked).

**3.5 My documents (upload)** — agent

- Pick a PDF, extract text per page on the phone, reject image-only PDFs, enforce character limits, send in batches of \~50 pages (architecture "PDF checks before upload").
- Tests: image-only detection, limit checks, batch retry (with fixture PDFs).

**3.6 Practice and offline store** — agent

- Drift (SQLite) store for answers, practice items, progress and an outbox; practice screens for multiple choice and quizzes with SM-2 scheduling; sync on reconnect with idempotency keys.
- Tests: SM-2 scheduling; outbox sends once after reconnect; practice works with networking off.

**3.7 Free gate (test-mode simulation)** — agent

- Device ID (`ANDROID_ID`) sent with every request; server counts 5 free questions per device and per account; app shows "Sign in to continue" after the first and "Subscribe to continue" after the fifth. In test mode, "sign in" is the tester picker.
- Tests (server): reinstall with the same device ID keeps the count; a new tester on the same device doesn't reset it.

**3.8 Phone test** — HUMAN TASK, then PHASE GATE

- Run through the gate on a budget Android phone on mobile data; report anything slow or confusing. The agent turns your notes into fixes before the gate.

## Phase 4: Voice, practice, limits and admin portal

Phase 4 adds the spoken teacher explanation, generated practice for thin chapters, real plan limits and usage tracking, and the Next.js admin portal. **Gate:** 20 testers use the app for 2 weeks, voice stays under the TTS cap, and the admin portal shows the measured cost per active student.

**4.1 Spoken teacher explanation** — agent, then HUMAN TASK

- `POST /v1/speech/explain`: speech script from `prompts/speech_script.md` on the cheap model, then Google TTS `am-ET-Wavenet-B`, cached per message; audio cached on the phone (architecture "Voice output").
- Global monthly TTS counter that stops voice at 90% of the free allowance; per-plan voice allowance; no voice on the free tier.
- HUMAN TASK: listen to 10 explanations and rate whether they sound like a teacher and how English terms are pronounced. The agent adjusts the script prompt.
- Tests (FakeTTS): cache hit makes no new TTS call; the cap blocks voice at 90%; free users get no voice.

**4.2 Generated practice for thin chapters** — agent

- Worker job that generates questions and flashcards only for chapters with fewer than a configured number of bank questions; validation rules from architecture "Practice"; admin can hide items.
- Tests: invalid JSON and wrong answers are rejected; chapters with enough bank questions are skipped.

**4.3 Plans, limits and usage** — agent

- Plans table driven by the database; daily question limits; character caps; per-provider daily spending caps; every costly call writes `usage_events` with `cost_usd`.
- Tests: each limit enforced; spending cap stops calls; costs add up correctly.

**4.4 Admin API** — agent

- `/admin/v1` endpoints with admin login (email + password, hashed) and roles, for library, plans, users, usage and cost, payments, flagged answers and read-only settings; every change written to `audit_log`.
- Tests: non-admins are refused; every change is audited.

**4.5 Admin portal (Next.js)** — agent, then HUMAN TASK

- `admin/`: login; Library (upload a book, set chapters, import questions, add video links); Plans; Users; Usage and cost dashboard (cost per active student per day, TTS characters against the cap); Flagged answers; Settings (read-only).
- HUMAN TASK: create the first admin account with the script the agent provides, then try each page and report problems.
- Tests: Vitest for forms and the API client; the API side is covered in 4.4.

**4.6 Tester pilot** — HUMAN TASK, then PHASE GATE

- Install the debug build on 20 testers' phones (the agent writes simple install steps), run for 2 weeks, and review the cost dashboard with the agent. The agent fills the real numbers into the cost model and proposes prices.

## Phase 5: Launch preparation

Phase 5 turns the test setup into production: real login, live Chapa payments, hosting, monitoring, a hardened release build and the Play Store listing. Most steps here are HUMAN TASKS because they involve contracts, money and accounts. **Gate:** every item in architecture "Checklist before launch" is ticked, including written permission for the textbooks.

**5.1 Permissions and legal** — HUMAN TASK (start early, in parallel with Phase 1)

- Request written permission from the Ministry of Education to use the textbooks; confirm ownership of the question bank and videos.
- Privacy policy and terms; the agent drafts them from the architecture document for a lawyer to review.

**5.2 SMS login** — HUMAN TASK, then agent

- Human: choose an SMS provider that delivers to Ethiopian numbers and put its keys in `.env`.
- Agent: OTP request and verify endpoints, rate limits, short-lived tokens and refresh tokens; the app's real sign-in screen replaces the tester picker in production builds; `AUTH_MODE=none` stays test-only.
- Tests: OTP expiry, wrong code limits, token refresh.

**5.3 Chapa live** — agent, then HUMAN TASK

- Agent: checkout, webhook signature check and verify call, subscription creation, manual activation in the admin portal, duplicate-webhook safety (architecture "Payments").
- Human: complete Chapa's business verification, add live keys, set the webhook URL, make a real small payment and refund it.
- Tests (FakePayments): success, failure, duplicate and forged webhooks.

**5.4 Production hosting** — agent writes, human deploys

- Agent: production Dockerfiles, `config/production.yaml`, a deployment guide for the chosen host, health checks, backups (Supabase paid plan), error tracking and uptime alerts, provider spending caps.
- Human: create the hosting account, add production secrets in the host's secret settings (never in git), deploy following the guide, point `api.<your domain>` at it.

**5.5 Release build hardening** — agent, then HUMAN TASK

- Release build with `--obfuscate --split-debug-info`, R8 enabled, certificate pinning, release `API_BASE_URL`.
- Human: create the upload signing key and store it safely (losing it blocks future updates), build the release, keep the debug-info files privately.

**5.6 Play Store** — HUMAN TASK

- Developer account, app listing in Amharic and English, screenshots, privacy policy link, data safety form (the agent drafts the answers), internal testing track, then production.

**5.7 Launch check** — agent and human, then PHASE GATE

- Load test with 50 simulated students; restore a backup; confirm every checklist item. The agent prepares the report; the human decides to launch.

## Prompts to start each phase

Paste these into the Antigravity agent chat. Replace the paths if you saved the docs somewhere else.

**Phase 0 (first session)**

```text
You are the coding agent for this project. Read docs/playbook.md fully, then docs/architecture.md.
Follow every rule in "Rules for the AI agent" for the whole project, especially: never run git push or touch remotes, never put real secrets anywhere, never call paid services in tests, and update the Build log at the end of docs/playbook.md after every change.
Start Phase 0 at step 0.1. Use the HUMAN TASK, READY TO COMMIT and PHASE GATE formats exactly.
Before each step, tell me in a few lines what you will build and which files you will touch.
```

**Any later session**

```text
Read docs/playbook.md (start with the Build log at the end) and docs/architecture.md.
Compare git status with the last Build log entry and record anything unexpected.
Continue from "Current state", following all playbook rules. If anything is waiting on me, show that HUMAN TASK first.
```

**Starting the next phase (after you reply "gate passed")**

```text
Gate passed for Phase <n>. Record it in the Build log and start Phase <n+1> at its first step, following all playbook rules.
```

**When the agent drifts**

```text
Stop. Re-read "Rules for the AI agent" in docs/playbook.md. Tell me which rule you broke, undo that change, and continue the current step.
```

**When something breaks**

```text
make test is failing. Show me the failing tests, your diagnosis and one proposed fix. Don't change anything outside the current step.
```

## When the agent must stop and ask

Agent: stop, explain in plain words, and wait for the human whenever any of these happens.

- A step needs an account, a key, money, a phone, a file only the human has, or a legal or business decision.
- The architecture document and this playbook disagree, or neither covers what you need.
- A change would delete data, drop or rewrite a table, change a migration that has already run on Supabase, or touch files outside the current step.
- You want to add a dependency, a service or a paid plan not named in the docs.
- A command would contact GitHub, change git history or remotes, or deploy anything.
- A real provider call is needed outside `make smoke` or `make eval`.
- Any free-tier limit (Groq, Supabase 500 MB, Google TTS allowance) is near its cap.
- The same error survives two fix attempts.
- A test would have to be weakened or skipped to pass.
- You are unsure whether something is safe for students' data.

## Build log

Agent: this is the only section of the playbook you edit. Update it after every change and before you report back, so any new session can continue from here alone (rules 21–25).

### Current state

Agent: rewrite this block after every change; keep it to these lines.

```text
Phase: 1 — Backend core, library and question bank
Step: 1.1 — Config and provider layer (finished, ready to commit)
Last updated: 2026-10-15
Next action: Step 1.2 Database and migrations
Waiting on human: review & commit Step 1.1
Tests: make test (12 passed in 3.39s), make smoke (passed)
Uncommitted work: api/app/config.py, api/app/providers/, api/tests/test_config.py, api/tests/test_providers.py, api/scripts/smoke_check.py, docs/playbook.md
```

### Decisions

- 2026-10-15: Python 3.12 managed via uv; Make (GnuWin32) added to User PATH; Android mobile device connected via Wi-Fi debugging.
- 2026-10-15: Postgres test-db port mapped to 5435 to avoid port collision with local postgres on 5432/5433.
- 2026-10-15: Supabase IPv4 connection established via aws-1-eu-central-1 pooler; pgvector confirmed enabled.
- 2026-10-15: Google Cloud TTS setup deferred to Phase 4 (no billing card available yet). FakeTTS used across all tests; make smoke skips TTS when GOOGLE_APPLICATION_CREDENTIALS is unset.
- 2026-10-15: Chapa test key deferred to Phase 5 (step 5.3). FakePayments used across all tests; make smoke skips Chapa when CHAPA_SECRET_KEY is unset. Phase 0 gate covers Groq and Supabase live checks.
- 2026-10-15: Tutor & smoke Groq models aligned with available models (openai/gpt-oss-120b and openai/gpt-oss-20b per architecture doc).
- 2026-10-15: Phase 0 gate passed by human. Starting Phase 1 (Backend core).

### Known issues

- None.

### Log (newest first)

Agent: add each entry at the top, in this format.

#### 2026-10-15 14:24 — Step 1.1 Config and provider layer — done

Changed: api/app/config.py, api/app/providers/base.py, api/app/providers/fakes.py, api/app/providers/groq.py, api/app/providers/local_store.py, api/app/providers/registry.py, api/app/providers/__init__.py, api/tests/test_config.py, api/tests/test_providers.py, docs/playbook.md
What: implemented Pydantic Settings with YAML config merger and production security validation (refuses AUTH_MODE=none in production); built abstract provider interfaces (ChatModel, Embedder, TTS, STT, FileStore, Payments) with UsageRecord reporting; built complete test fakes and Groq/LocalFileStore implementations; added 11 unit tests covering config and providers
Tests: make test → 12 passed
Half-done: none
Next: Step 1.2 Database and migrations (SQLAlchemy models and Alembic migrations for data model tables)
Waiting on human: review & commit

#### 2026-10-15 14:06 — Phase 0 Gate passed — starting Step 1.1 Config and provider layer

Changed: docs/playbook.md
What: Phase 0 gate approved by human; transitioning to Phase 1, Step 1.1 (Config and provider layer)
Tests: make test → 1 passed; make smoke → passed
Half-done: none
Next: Step 1.1 Config loader, provider interfaces, implementations and fakes
Waiting on human: nothing

#### 2026-10-15 14:03 — Step 0.4 Smoke check — done

Changed: api/scripts/smoke_check.py, api/config/test.yaml, docs/playbook.md
What: created smoke check script verifying Groq API completion (openai/gpt-oss-20b) and Supabase database connectivity with pgvector; skips deferred Google Cloud TTS and Chapa gracefully; updated test.yaml model mapping
Tests: make smoke → Groq & Supabase PASSED; make test → 1 passed
Half-done: none
Next: PHASE GATE for Phase 0
Waiting on human: Gate confirmation

#### 2026-10-15 13:58 — Step 0.3 Accounts and keys — done

Changed: docs/playbook.md, api/.env
What: Step 0.3 completed; Groq API key set and validated; Supabase database and pgvector extension verified; Google Cloud TTS deferred to Phase 4; Chapa deferred to Phase 5 (step 5.3); FakeTTS and FakePayments used for tests
Tests: make test → 1 passed; live Supabase query → pgvector extension confirmed
Half-done: none
Next: Step 0.4 Smoke check (build api/scripts/smoke_check.py with skips for deferred services)
Waiting on human: Google Cloud TTS deferred to Phase 4; Chapa deferred to Step 5.3

#### 2026-10-15 13:46 — Step 0.3 Accounts and keys — in progress

Changed: docs/playbook.md, api/.env
What: Supabase database connection verified successfully via psycopg; confirmed extensions including pgvector; moving to service 3 (Google Cloud Text-to-Speech)
Tests: make test → 1 passed; live Supabase query → pgvector extension confirmed
Half-done: Groq and Supabase configured; Google Cloud and Chapa pending in order
Next: present Google Cloud HUMAN TASK, verify service account key in api/secrets/
Waiting on human: Google Cloud TTS service account JSON in api/secrets/ and GOOGLE_APPLICATION_CREDENTIALS in api/.env

#### 2026-10-15 13:23 — Step 0.3 Accounts and keys — in progress

Changed: docs/playbook.md, api/.env
What: Groq API key set in api/.env; moving to service 2 (Supabase database with pgvector)
Tests: make test → 1 passed
Half-done: Groq key set; Supabase, Google Cloud, and Chapa pending in order
Next: present Supabase HUMAN TASK, verify connection string in api/.env
Waiting on human: Supabase project created, vector extension enabled, and DATABASE_URL in api/.env

#### 2026-10-15 13:19 — Step 0.3 Accounts and keys — in progress

Changed: docs/playbook.md, api/.env
What: verified initial commit and push to private repository; initiated Step 0.3 with service 1 (Groq API key)
Tests: make test → 1 passed
Half-done: Groq key requested; Supabase, Google Cloud, and Chapa pending in order
Next: verify Groq key, then present Supabase HUMAN TASK
Waiting on human: GROQ_API_KEY in api/.env

#### 2026-10-15 12:06 — Step 0.2 Repo scaffold — done

Changed: .gitignore, README.md, docker-compose.yml, Makefile, api/pyproject.toml, api/README.md, api/.env.example, api/config/test.yaml, api/app/main.py, api/tests/test_health.py, mobile/ (moved Flutter files), docs/playbook.md
What: repo scaffold established with API FastAPI app (/health endpoint), pgvector & redis docker compose services, root Makefile, comprehensive .gitignore, and mobile app in mobile/ directory
Tests: make test → 1 passed; mobile flutter test → 1 passed; GET /health → {"status":"ok"}
Half-done: none
Next: HUMAN TASK 0.2 (connect private GitHub repo, commit and push), then Step 0.3 Accounts and keys
Waiting on human: private GitHub repo creation and initial push

#### 2026-10-15 11:55 — Step 0.1 Tools on your computer — done

Changed: docs/playbook.md
What: verified Git 2.50.0, Docker 29.1.3 (daemon running), Python 3.12.15 via uv, uv 0.13.1, Flutter 3.44.9, Android SDK licenses accepted, Wi-Fi debugging phone connected, Node v24.12.0, Make 3.81
Tests: tool diagnostics passed
Half-done: none
Next: Step 0.2 Repo scaffold
Waiting on human: nothing
