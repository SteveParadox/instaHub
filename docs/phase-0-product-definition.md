# Phase 0 — Product Definition

## V1 outcome
A creator can sign in, create a workspace, generate an AI image, save it to a media library, create a caption/hashtags, connect Instagram or Pinterest, then publish immediately or schedule a single-image post.

## In scope
- Email/password sign-in through Supabase Auth
- Personal workspace and profile
- Prompt-to-image generation through one provider adapter
- Media library, asset variants, captions and hashtags
- Instagram Business/Creator and Pinterest account connections
- Publish now, scheduled publishing, publishing status and retry-tracked attempts
- Usage events, request IDs, structured failure diagnostics and workspace authorization

## Explicitly deferred
- Live video generation adapters and video publishing UI (the schema/contracts are ready)
- Carousels, Stories, and additional social platforms
- Collaborative approval flows, paid subscriptions, workflow automations, deep analytics
- Advanced provider adapters beyond the active OpenAI implementation

## User stories and acceptance criteria
| Story | Done when |
|---|---|
| Sign up | User can authenticate and reaches a workspace dashboard. |
| Create image | User submits a prompt, sees a queued/running/completed job, and receives an image asset. |
| Save image | Completed output appears in the workspace media library with metadata. |
| Generate caption | User can request editable caption + hashtags associated with an asset. |
| Connect Instagram | OAuth connects an eligible Instagram professional account and securely stores tokens. |
| Publish now | A validated image + caption is published once; the external ID and response are retained. |
| Schedule later | User selects a future time; worker publishes once and reports success/failure. |

## Provider shortlist
| Capability | V1 choice | Alternatives kept behind adapters |
|---|---|---|
| Image generation/editing | OpenAI Images API | fal.ai, Replicate, Stability, FLUX providers |
| Caption + hashtags | OpenAI Chat Completions | Anthropic, Gemini |
| Image transformations | OpenAI edits + local crop/upscale | fal.ai, Replicate, Cloudinary |
| Storage | Cloudflare R2 | AWS S3 |
| Auth | Supabase Auth | Clerk |
| Video later | — | Runway, Kling, Veo, fal.ai, Replicate |

## Instagram constraints to design around
- Publishing is available through Meta's APIs for eligible professional Instagram accounts, not ordinary personal accounts.
- The user must complete Meta OAuth and grant the needed permissions; tokens can expire or be revoked and must be refreshed/reconnected safely.
- Publicly reachable media URLs are required by the publishing flow, so private originals need signed/public delivery strategy.
- Media must pass Meta-supported format, size, aspect-ratio and caption requirements. Validate before queuing.
- Publishing is asynchronous: create container, poll/status-check, then publish. Store every attempt and use idempotency keys to prevent duplicates.
- API permissions, app review and production access are launch gates; use Meta sandbox/test accounts during development.
- Scheduling should use the platform's permitted flow and a server-side worker; never rely on a browser session staying open.

## Wireframes

### Dashboard
```text
┌ Sidebar ─────┬──────────────────────────────────────┐
│ Dashboard    │ Good evening, Stephen       [+ Create] │
│ Create       ├──────────────────────────────────────┤
│ Library      │ Usage this month   | Connected account │
│ Calendar     ├──────────────────────────────────────┤
│ Settings     │ Recent assets                         │
└──────────────┴──────────────────────────────────────┘
```

### Create and publish
```text
┌ Prompt + style controls ──┬──── Live result ────────┐
│ “A chrome sports car...”  │          [image]         │
│ [Generate]                │ [Edit] [Upscale] [Save]  │
├───────────────────────────┴─────────────────────────┤
│ Caption editor + hashtags        [Publish] [Schedule]│
└─────────────────────────────────────────────────────┘
```

## Success metrics
- Time from prompt submission to saved asset
- Generation completion/failure rate and provider cost per asset
- Connected Instagram accounts
- Scheduled-post success rate and duplicate-publish count (target: zero)
