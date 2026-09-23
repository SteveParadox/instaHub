# Architecture

```mermaid
flowchart TD
  Web["Next.js web app"] --> API["FastAPI API"]
  API --> DB["PostgreSQL"]
  API --> Queue["Redis + worker queue"]
  API --> Storage["S3/R2 storage"]
  Queue --> Providers["AI provider adapters"]
  Queue --> Meta["Instagram Graph API"]
  API --> Auth["Supabase Auth"]
```

## Boundary rules
- The browser speaks only to the FastAPI API and Supabase Auth.
- Connector adapters own provider-specific request/response code.
- Workers perform long-running generation, scheduling and publishing.
- Media files live in object storage; the database only stores metadata and keys.
- Webhooks verify signatures before changing job or publish state.
