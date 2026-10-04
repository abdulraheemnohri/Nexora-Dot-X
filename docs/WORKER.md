# Always-On Background Worker

nexora start now launches the web control center AND a background worker:

    Scheduler: runs due schedules -> creates tasks
    Channels:  polls Telegram getUpdates (if NEXORA_SECRET_TELEGRAM_TOKEN set)
    Profile:  controls polling interval and concurrency

Device profiles (NEXORA_PROFILE / --profile):

| Profile | Workers | Context | Poll | Browser | Parallel tasks |
|---------|---------|---------|------|---------|----------------|
| battery-saver | 1 | 1024 | 60s | no | 1 |
| balanced | 4 | 4096 | 10s | yes | 4 |
| performance | 8 | 8192 | 2s | yes | 8 |

Every message received via Telegram becomes a queued task and gets a
confirmation reply with the task id.
