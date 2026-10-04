# Authentication

Optional. Enable with `NEXORA_AUTH_ENABLED=true`.

## Password
```bash
python -m nexora.security set-password    # sets NEXORA_SECRET_PASSWORD_HASH
```
Or generate a hash with `AuthManager.hash_password()` and export it yourself.

## Behavior when enabled
- Pages require a session cookie (`/login` form, 12h TTL)
- API routes accept `Authorization: Bearer <token>` where token =
  `NEXORA_SECRET_API_TOKEN`; otherwise 401
- `/login` and static assets stay open

## API example
```bash
curl -H "Authorization: Bearer $NEXORA_SECRET_API_TOKEN" \
  http://127.0.0.1:8000/api/status
```

Disabled (default): everything stays open for local single-user use.
