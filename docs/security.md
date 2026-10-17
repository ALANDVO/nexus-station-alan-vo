# Security Considerations

## Current State

### Local Demo Auth (Round 1)

The current implementation uses a local-only demo authentication mode:

- `AUTH_MODE=local` (default): validates a shared-secret API key via the
  `Authorization: Bearer <key>` header. Binds to `127.0.0.1` only.
- `AUTH_MODE=production`: **refuses to start** without `OIDC_DISCOVERY_URL`
  configured. Raises HTTP 501 if OIDC is requested but not implemented.
- No hardcoded credentials are committed. The `.env.example` template uses
  placeholder values.
- The default `LOCAL_API_KEY=dev-only-key` is for development only.

### What's Not Yet Implemented

- Full OIDC authorization-code login with Keycloak (state + nonce + PKCE)
- JWT signature/issuer/audience validation
- HttpOnly SameSite cookies or SPA PKCE token management
- Session management
- Role-based authorization beyond the single-key demo model

## Planned Security Model

### OIDC / Keycloak (Future Milestone)

- Authorization-code flow with `state + nonce + PKCE`
- Two architecture options under consideration:
  1. **Backend-managed sessions**: HttpOnly SameSite cookies + CSRF protection
  2. **SPA PKCE**: Access tokens kept in memory (sessionStorage for state only)
- Roles: `viewer`, `analyst`, `operator`, `admin`
- SAML identity brokering through Keycloak for upstream IdPs
- Demo mode refuses to start in production (`AUTH_MODE=production` requires OIDC)

### LLM Security

- LLM API keys (`LLM_API_KEY`) are server-side only — never sent to client
- Bounded timeouts on all LLM requests
- Errors are redacted — no token material in error messages
- Advisory labels distinguish LLM-generated content from stored records

## Threat Model (Partial)

- **Network**: API binds to localhost in demo mode. Production requires TLS
  termination at a reverse proxy.
- **Storage**: SQLite database file. Backups should be encrypted at rest.
- **Input**: All user inputs validated via Pydantic models. SQL queries use
  parameterized statements throughout.
- **Audit**: All mutations recorded in `audit_log` table with timestamps.