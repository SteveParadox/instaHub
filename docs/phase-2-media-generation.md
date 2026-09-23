# Phase 2 media generation
The API creates a queued job. Celery consumes it from Redis, calls the OpenAI image adapter, uploads each output to S3/R2, writes media assets, and marks the job completed or failed. The browser polls the job every two seconds and renders completed assets.

Set OPENAI_API_KEY plus S3/R2 credentials, bucket, and S3_PUBLIC_BASE_URL in .env. Start the worker with: celery -A app.tasks.celery worker --loglevel=INFO.
