# Phases 7 and 8
Scheduling stores timezone-aware future dates, supports edit/cancel/list operations, and Celery Beat dispatches due posts every minute to the existing publishing workers.

The provider registry exposes provider capabilities and models. Workspace default selection validates that a connector exists, retains OpenAI as fallback, and usage events are ready for per-provider cost/credit recording. Admin enable/disable is represented by the registry enabled flag; move it to a database-backed admin control when RBAC administration is introduced.