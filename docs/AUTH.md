# Authentication

By default Nexora runs local single-user with auth disabled
(NEXORA_AUTH_ENABLED=false) - it binds to 127.0.0.1 only.

To enable auth:

1. Generate a password hash:

       nexora password

2. Put it in .env:

       NEXORA_AUTH_ENABLED=true
       NEXORA_SECRET_PASSWORD_HASH=<output>

3. Restart; all web sessions now require login at /login.

API tokens: set NEXORA_SECRET_API_TOKEN and send
"Authorization: Bearer <token>" on API calls.

Passwords are PBKDF2-SHA256 hashed (100k iterations, per-password salt).
Session tokens are random, httpOnly cookies, 12h TTL.
