# Pinterest connector
Pinterest uses OAuth authorization-code flow with encrypted access and refresh tokens. It requests user account, board read, and pin read/write scopes. The UI fetches boards, and both immediate and scheduled image publishing create tracked, retryable attempts through the worker queue.

Configure PINTEREST_APP_ID, PINTEREST_APP_SECRET, and PINTEREST_REDIRECT_URI exactly in the Pinterest developer app. Pinterest requires app access approval; use its sandbox/trial flow before production.
