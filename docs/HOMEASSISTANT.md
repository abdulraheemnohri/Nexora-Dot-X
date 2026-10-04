# Home Assistant (optional)

Configure:

    NEXORA_SECRET_HA_URL=http://homeassistant.local:8123
    NEXORA_SECRET_HA_TOKEN=<long-lived access token>

Capabilities:
- List states / devices (read-only, safe)
- Call services: routed through System 1 - service calls require user
  approval unless explicitly allow-listed.
