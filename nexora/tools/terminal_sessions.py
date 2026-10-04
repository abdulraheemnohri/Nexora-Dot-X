"""Persistent terminal sessions for the UI terminal page."""
import time
from collections import deque
from nexora.tools.terminal import TerminalTool
from nexora.core.events import bus


class TerminalSession:
    def __init__(self, session_id: str, cwd: str = "."):
        self.id = session_id
        self.tool = TerminalTool(cwd)
        self.history: deque = deque(maxlen=200)
        self.created_at = time.time()

    def run(self, command: str) -> dict:
        result = self.tool.run(command)
        self.history.append({"command": command, "ok": result["ok"],
                             "output": result["output"], "ts": time.time()})
        bus.publish("terminal.exec", {"session": self.id, "command": command,
                                      "ok": result["ok"]})
        return result


class TerminalSessionManager:
    def __init__(self, cwd: str = "."):
        self._sessions: dict[str, TerminalSession] = {}

    def create(self, session_id: str, cwd: str = ".") -> TerminalSession:
        s = TerminalSession(session_id, cwd)
        self._sessions[session_id] = s
        return s

    def get(self, session_id: str) -> TerminalSession | None:
        return self._sessions.get(session_id)

    def list(self) -> list:
        return list(self._sessions.values())

    def close(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None
