# Phases 7 and 8
Scheduling stores timezone-aware future dates, supports edit/cancel/list operations, and Celery Beat claims due posts every 30 seconds before dispatching them to the Instagram or Pinterest worker.

The provider registry exposes provider capabilities and models. Workspace owners can select a connected, deployment-enabled default. Requests fail explicitly when a selected adapter is unavailable instead of silently switching providers. Image, edit, and caption operations write provider usage events. Global provider enable/disable remains configuration-backed until application-admin RBAC is introduced.
