# Phase 2 media generation and AI connectors
The API queues image jobs, Celery generates and stores them, and the browser polls for results.

## Workspace connectors
Users can connect OpenAI from the UI using their own API key. The server validates the key, encrypts it using CREDENTIAL_ENCRYPTION_KEY, and saves only the encrypted value in ai_provider_accounts. The browser never receives the stored key.

The same OpenAI connector powers image generation plus caption and hashtag generation. The catalog deliberately exposes future fal.ai and Replicate entries with their capabilities, while their adapters are added in later phases.

Set OPENAI_API_KEY for a platform-managed default or let each workspace connect its own key. Set CREDENTIAL_ENCRYPTION_KEY to a Fernet key generated with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())".
