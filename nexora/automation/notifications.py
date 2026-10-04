"""Notification dispatcher: web/event bus + configured channels."""
from nexora.core.events import bus


class Notifier:
    def notify(self, event: str, message: str, dot_id=None):
        bus.publish("notification", {"event": event, "message": message,
                                     "dot_id": dot_id})
        self._push_channels(event, message)

    def _push_channels(self, event: str, message: str):
        """Best-effort delivery to opt-in channels; local-only safe."""
        import os
        try:
            chat = os.getenv("NEXORA_SECRET_NOTIFY_TELEGRAM_CHAT")
            if os.getenv("NEXORA_SECRET_TELEGRAM_TOKEN") and chat:
                from nexora.channels.telegram import TelegramChannel
                TelegramChannel().send(chat, "[" + event + "] " + message)
        except Exception:
            pass
        try:
            import subprocess
            import platform
            if (platform.system() == "Linux"
                    and os.getenv("NEXORA_DESKTOP_NOTIFY") == "1"):
                subprocess.run(["notify-send", event, message], timeout=5)
        except Exception:
            pass


notifier = Notifier()
