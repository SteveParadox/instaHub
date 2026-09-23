# Data model

All data is workspace-scoped. UUID primary keys, UTC timestamps, and `created_at`/`updated_at` fields are standard.

## Identity and organization
- `users`: id (Supabase user id), email, display_name, plan
- `workspaces`: id, name, owner_id
- `workspace_members`: workspace_id, user_id, role
- `brand_profiles`: workspace_id, name, tone, style_preferences, hashtag_preferences, caption_rules, prompt_defaults

## Connectors
- `ai_provider_accounts`: workspace_id, provider_name, encrypted_api_key, settings_json, is_active
- `social_accounts`: workspace_id, platform, account_name, external_account_id, encrypted_access_token, encrypted_refresh_token, token_expires_at, metadata_json

## Media
- `projects`: workspace_id, name, type
- `generation_jobs`: workspace_id, project_id, provider_name, model_name, media_type, prompt, negative_prompt, settings_json, status, external_job_id, created_by, completed_at
- `media_assets`: workspace_id, generation_job_id, media_type, storage_key, delivery_url, thumbnail_url, preview_url, width, height, duration_seconds, fps, aspect_ratio, file_size, mime_type, processing_status, transcode_status, metadata_json
- `asset_variants`: parent_asset_id, variant_type, storage_key, metadata_json

## Publishing
- `posts`: workspace_id, media_asset_id, caption, first_comment, platform, status, scheduled_at, published_at, created_by
- `post_targets`: post_id, social_account_id, platform_specific_settings_json
- `publish_attempts`: post_id, social_account_id, idempotency_key, external_post_id, status, response_json, error_message

## Governance
- `usage_events`: workspace_id, user_id, event_type, provider_name, credits_used, cost_estimate, metadata_json
- `audit_events`: workspace_id, actor_id, action, entity_type, entity_id, metadata_json
- `automation_rules`: workspace_id, name, trigger_type, action_type, config_json, is_active

## Important constraints
- `media_type` is an enum: image, video, carousel, story, reel.
- Tokens and provider keys are encrypted at rest and never returned by the API.
- A unique index on `publish_attempts.idempotency_key` prevents duplicate delivery.
- Every queue operation is tied to a workspace, user, and audit event.
