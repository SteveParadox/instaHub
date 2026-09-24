# instaHub

AI Creator Studio for Instagram — generate, organize, caption, publish, schedule, and later automate AI content.

## Stack

- **Web:** Next.js, TypeScript, Tailwind CSS
- **API:** FastAPI, SQLAlchemy, Alembic
- **Data:** PostgreSQL, Redis
- **Workers:** Celery worker + beat scheduler
- **Auth:** Supabase Auth
- **Storage:** S3-compatible bucket (Cloudflare R2 or AWS S3)
- **Billing:** Stripe-ready direction (not implemented yet)
- **Publishing:** Instagram Graph API and Pinterest API

## Quick start

1. Copy `.env.example` to `.env` and supply real values.
2. Start local dependencies: `docker compose up -d db redis`.
3. Start API: `cd apps/api && python -m venv .venv && .venv/bin/pip install -e '.[dev]' && .venv/bin/alembic upgrade head && .venv/bin/uvicorn app.main:app --reload`.
4. Start web: `corepack enable && pnpm install && pnpm --filter @instahub/web dev`.

To run the complete backend stack, use `docker compose up --build`; this starts the API, worker, scheduler, PostgreSQL, and Redis. New schema changes must be added as Alembic revisions—application startup does not mutate the database.

See [Phase 0 product definition](docs/phase-0-product-definition.md), [data model](docs/data-model.md), and [architecture](docs/architecture.md).
