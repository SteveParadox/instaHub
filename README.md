# instaHub

AI Creator Studio for Instagram — generate, organize, caption, publish, schedule, and later automate AI content.

## Stack

- **Web:** Next.js, TypeScript, Tailwind CSS
- **API:** FastAPI, SQLAlchemy, Alembic
- **Data:** PostgreSQL, Redis
- **Workers:** Celery (planned worker entrypoint)
- **Auth:** Supabase Auth
- **Storage:** S3-compatible bucket (Cloudflare R2 or AWS S3)
- **Billing:** Stripe
- **Publishing:** Instagram Graph API

## Quick start

1. Copy `.env.example` to `.env` and supply real values.
2. Start local dependencies: `docker compose up -d db redis`.
3. Start API: `cd apps/api && python -m venv .venv && .venv/bin/pip install -e . && .venv/bin/uvicorn app.main:app --reload`.
4. Start web: `corepack enable && pnpm install && pnpm --filter @instahub/web dev`.

See [Phase 0 product definition](docs/phase-0-product-definition.md), [data model](docs/data-model.md), and [architecture](docs/architecture.md).
