"""Append-oriented audit log for every sensitive operation."""
import json
from datetime import datetime, timezone
from nexora.database.models import AuditLog
from nexora.database import repositories as repo


def audit(actor: str = "system", *, bot_id=None, task_id=None,
          tool: str = "", action: str = "", decision: str = "", outcome: str = "") -> AuditLog:
    entry = AuditLog(actor=actor, bot_id=bot_id, task_id=task_id,
                     tool=tool, action=action, decision=decision, outcome=outcome)
    return repo.add_obj(entry)


def tail(limit: int = 200) -> list:
    return repo.get_all(AuditLog, limit=limit, order_desc="created_at")


def render(entry: AuditLog) -> str:
    ts = datetime.fromtimestamp(entry.created_at, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return json.dumps({"ts": ts, "actor": entry.actor, "tool": entry.tool,
                       "action": entry.action, "decision": entry.decision,
                       "outcome": entry.outcome}, ensure_ascii=False)
