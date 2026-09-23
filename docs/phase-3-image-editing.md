# Phase 3 image editing
Editing never overwrites a source media asset. Every action creates a queued asset operation and later an immutable asset variant.

Supported operations:
- variation: prompt-guided new creative version via OpenAI
- edit: prompt-guided edit via OpenAI
- background_remove: prompt-guided background removal via OpenAI
- upscale: local high-quality Lanczos upscale
- crop: centre crop for chosen Instagram aspect ratio

The API creates an operation, Celery runs it, and clients poll its status. Region-mask regeneration is intentionally deferred until the editor includes a mask-selection UI and storage format.
