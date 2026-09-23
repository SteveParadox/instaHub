# Phase 6 Instagram publishing
Publishing uses the generated asset's public HTTPS URL. A post and a unique publish attempt are written before a Celery worker creates an Instagram media container and publishes it. Attempts track queued, publishing, published or failed states, external IDs, platform response, and diagnostics.

Retries retain the same attempt and idempotency key. A source asset is never republished automatically after a successful attempt.
