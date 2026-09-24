# Data model

All creator data is workspace-scoped. UUID primary keys, UTC timestamps, and `created_at`/`updated_at` fields are standard. Workspace membership is enforced in the API rather than trusting client-supplied workspace IDs.

## Identity and organization
- `users`: Supabase user ID, email, name
- `workspaces`: name, owner, default AI provider
- `workspace_members`: workspace, user, role
- `brand_profiles`: workspace, tone, visual DNA, prompt defaults, reference assets
- `personas`: brand profile, role, appearance, voice rules, consistency memory

## Connectors
- `ai_provider_accounts`: workspace, provider, encrypted API key, settings, active state
- `social_accounts`: workspace, platform, external account ID, encrypted access/refresh tokens, expiry, metadata

## Media and generation
- `generation_jobs`: workspace, provider/model, media type, prompt, settings, status, provider job ID, creator, completion time
- `video_generation_jobs`: workspace, provider/model, prompt, progress, provider job ID, reference settings, output asset
- `media_assets`: workspace, media type, object key/public URL, thumbnail/preview, dimensions, duration, FPS, aspect ratio, processing/transcode state, MIME type, metadata
- `asset_operations`: source asset, operation, creator, settings, status, output variant
- `asset_variants`: immutable child version, operation, object key/public URL, dimensions, metadata
- `caption_drafts`: workspace, source text, caption, hashtags, options, creator

## Publishing
- `posts`: workspace, asset, caption, platform, platform settings, state, scheduled/published times, creator
- `publish_attempts`: post, social account, idempotency key, retry count, external post ID, response metadata, diagnostics

## Governance
- `usage_events`: workspace, user, event type, provider, credits, estimated cost, metadata

## Important constraints
- `media_assets.media_type` keeps the library media-agnostic; image is active and video metadata is ready.
- Tokens and provider keys are encrypted at rest and never returned by the API.
- A unique constraint on `publish_attempts.idempotency_key` protects each tracked delivery attempt.
- Alembic owns schema evolution; application startup does not call `create_all`.

Projects, approval workflows, audit events, automation rules, carousels, and billing records remain planned rather than implemented tables.
