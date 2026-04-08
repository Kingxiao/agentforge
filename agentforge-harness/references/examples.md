# Real-World CLAUDE.md Examples

## Example 1: Full-Stack Web Application (Next.js + Prisma)

```markdown
# TaskFlow — Project Management App

Next.js 14 app router + Prisma + PostgreSQL + Tailwind CSS + TypeScript.

## Commands
- Dev: `npm run dev`
- Build: `npm run build`
- Test: `npm test`
- Lint: `npm run lint`
- DB migrate: `npx prisma migrate dev`
- DB seed: `npx prisma db seed`

## Architecture
App router with RSC. Server actions for mutations. Prisma for data access.
Route groups: `(auth)` for protected, `(public)` for open pages.

## Rules
- Server components by default. Add "use client" only when hooks or interactivity needed.
- All database access through Prisma. No raw SQL.
- Validate inputs with Zod schemas in `src/lib/validations/`.
- Error boundaries in every route segment.

## Known Pitfalls
- Prisma client must be singleton in dev (see `src/lib/prisma.ts`).
- Next.js caches aggressively. Use `revalidatePath()` after mutations.
- Tailwind classes must be complete strings. Dynamic class construction breaks purge.
```

## Example 2: Python Backend API (FastAPI)

```markdown
# InventoryAPI — Warehouse Management Service

FastAPI + SQLAlchemy + Alembic + pytest. Python 3.12.

## Commands
- Run: `uvicorn src.main:app --reload`
- Test: `python -m pytest -x -v`
- Lint: `ruff check src/`
- Format: `black src/`
- Type check: `mypy src/`
- Migration: `alembic revision --autogenerate -m "description"`

## Architecture
Layered: routers → services → repositories → models.
Routers handle HTTP. Services contain business logic. Repositories handle DB.
Services never import from routers. Repositories never import from services.

## Rules
- All endpoints must have Pydantic request/response models.
- All repository methods are async.
- Tests use fixtures from `tests/conftest.py`. Never create test DB connections manually.
- Environment variables accessed only through `src/config.py`.

## Known Pitfalls
- SQLAlchemy async sessions must use `async with` pattern. Forgetting causes connection leaks.
- Alembic migrations require running DB. Start Docker first: `docker compose up db -d`.
- Async tests: use `@pytest.mark.anyio` (from `anyio`, recommended by FastAPI docs) or `@pytest.mark.asyncio` (from `pytest-asyncio`). Don't mix the two plugins.
```

## Example 3: Mobile App (React Native + Expo)

```markdown
# FitTrack — Fitness Tracking App

Expo SDK 52 + React Native + TypeScript + Zustand + React Query.

## Commands
- Dev: `npx expo start`
- Test: `npm test`
- Lint: `npx eslint .`
- Type check: `npx tsc --noEmit`
- EAS build: `eas build --platform ios`

## Architecture
Feature-based folders under `src/features/`. Each feature has its own screens, components, hooks, and API calls. Shared code in `src/shared/`.

## Rules
- Navigation types defined in `src/navigation/types.ts`. All screens must be typed.
- Use Zustand for global state. React Query for server state. Never mix them.
- All API calls through `src/shared/api/client.ts`. Never use fetch directly.
- Platform-specific code uses `.ios.tsx` / `.android.tsx` extensions, not runtime checks.

## Known Pitfalls
- Expo modules must be installed with `npx expo install`, not `npm install`.
- React Native doesn't support all CSS. `gap` works on SDK 52+ but older RN versions require `marginBottom` on children.
- Async storage is limited to strings. Always JSON.stringify/parse.
```

## Example 4: CLI Tool (Rust)

```markdown
# logparse — High-Performance Log Analysis Tool

Rust 1.78 + clap + tokio + serde.

## Commands
- Build: `cargo build`
- Test: `cargo test`
- Run: `cargo run -- [args]`
- Lint: `cargo clippy -- -D warnings`
- Format: `cargo fmt`
- Bench: `cargo bench`

## Architecture
Binary crate in `src/main.rs`. Core library in `src/lib/`.
Modules: parser (log format detection), filter (query engine), output (formatters).

## Rules
- No unwrap() in library code. Use `anyhow::Result` for error propagation.
- All public APIs must have doc comments with examples.
- New features require both unit tests and integration tests in `tests/`.
- Performance-critical paths must have benchmarks in `benches/`.

## Known Pitfalls
- Tokio runtime must be multi-threaded for file I/O parallelism: `#[tokio::main]`.
- Large file parsing must use streaming (BufReader), not read_to_string.
- Clippy pedantic mode catches real issues. Fix all warnings before commit.
```

## Example 5: Minimal Starter (Any Project)

When starting from scratch with no known pitfalls yet:

```markdown
# [Project Name]

[One sentence description].

## Stack
[List technologies]

## Commands
- Build: `[command]`
- Test: `[command]`
- Lint: `[command]`

## Rules
[Leave minimal — add rules only as failures occur]

## Pitfalls
[Empty — populate through the Hashimoto Loop]
```

This is the minimum viable harness. It will grow organically as agent failures reveal what's missing.
