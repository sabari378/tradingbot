# Security

- Paper mode is the default and live mode is not implemented.
- Never log or commit passwords, tokens, API keys, or broker credentials.
- Keep the MT5 gateway on `127.0.0.1:8100` initially and authenticate every order request.
- Every trade and execution request uses a UUID and must be idempotent.
- Reject duplicate, stale, unapproved, risk-rejected, or non-demo orders.
- Keep audit records immutable at the application layer.
- Protect approval, execution, close, account, and voice execution endpoints with API-key authentication during development.
- Voice commands may not execute arbitrary shell commands; execution intents require confirmation and stronger authentication.
