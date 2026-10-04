# WebSocket API

Connect to ws://host:port/ws to receive live JSON events:

    {"kind": "task.status", "payload": {"id": "...", "status": "RUNNING"}}
    {"kind": "approval.requested", "payload": {...}}
    {"kind": "notification", "payload": {...}}

All events published on the internal EventBus fan out to connected clients,
so the Activity view, task pages and approval prompts can update live.
