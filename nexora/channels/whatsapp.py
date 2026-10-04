"""WhatsApp provider abstraction: vendor-agnostic adapter interface.

Concrete vendors (e.g. Baileys bridge, cloud API) implement WhatsAppAdapter;
all of them route through the Gateway + System 1. Explicit opt-in only.
"""
from nexora.channels.gateway import Channel
from nexora.core.task_engine import TaskEngine


class WhatsAppAdapter(Channel):
    name = "whatsapp"

    def enabled(self) -> bool:
        return False  # explicit opt-in per deployment

    def verify_sender(self, sender: str) -> bool:
        allow = getattr(self, "_allowed_senders", set())
        return sender in allow

    def receive(self, message: dict) -> dict:
        sender = message.get("sender", "")
        if not self.enabled() or not self.verify_sender(sender):
            return {"ok": False, "error": "whatsapp channel not enabled/sender not verified"}
        goal = (message.get("text") or "").strip()
        if not goal:
            return {"ok": False, "error": "empty message"}
        t = TaskEngine().create(goal, dot_id=message.get("dot_id"))
        return {"ok": True, "task_id": t.id}
