"""WebSocket hub: live activity, task updates, approval events."""
import asyncio
import json


class WebSocketHub:
    def __init__(self):
        self._clients: set = set()
        self._loop = None

    def bind_loop(self, loop):
        self._loop = loop

    async def connect(self, websocket):
        self._clients.add(websocket)

    def disconnect(self, websocket):
        self._clients.discard(websocket)

    def broadcast(self, kind: str, payload: dict):
        """Thread-safe broadcast; safe to call from sync code (event bus)."""
        if not self._clients:
            return
        msg = json.dumps({"kind": kind, "payload": payload}, ensure_ascii=False)
        if self._loop is not None:
            try:
                asyncio.run_coroutine_threadsafe(self._send_all(msg), self._loop)
            except Exception:
                pass

    async def _send_all(self, msg: str):
        dead = []
        for ws in list(self._clients):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


hub = WebSocketHub()
