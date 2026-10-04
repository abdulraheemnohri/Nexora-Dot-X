# Streaming Chat

Two chat paths:

1. HTMX form (POST /api/chat): returns the full reply into the page,
   no JS required.
2. WebSocket (/ws/chat): token-by-token streaming.

    ws = new WebSocket("ws://host:port/ws/chat");
    ws.send(JSON.stringify({"kind": "chat.message",
                            "dot_id": "...", "message": "hi"}));

Events received: chat.start -> chat.chunk* -> chat.done (or chat.error).
If no model is ready, a chat.error is sent with install instructions -
Nexora never fakes a reply.
