# Channels

All channels route through the Gateway:

    message -> identity -> Dot -> Task -> System 1

Enabled per deployment via secrets (environment variables, never stored in DB):

| Channel | Secret |
|---------|--------|
| Telegram | NEXORA_SECRET_TELEGRAM_TOKEN |
| Discord  | NEXORA_SECRET_DISCORD_TOKEN |
| Slack    | NEXORA_SECRET_SLACK_BOT_TOKEN |
| Email    | NEXORA_SECRET_SMTP_HOST/USER/PASSWORD/FROM |

Email sending always requires System 1 approval (AS-level risk).
WhatsApp is a vendor-agnostic adapter with explicit opt-in + sender verification.
