"""Persistent always-allow grants (System 1).

User "always allow" grants from the approval center are stored in SQLite so
they survive restarts. A module-level in-memory set remains the hot path for
evaluation; this module keeps that set synchronized with the database.
"""
from nexora.control.policy import ALWAYS_ALLOWED
from nexora.database.models import AlwaysAllow
from nexora.database import repositories as repo


def normalize(tool: str, action: str) -> tuple:
    return (tool, " ".join((action or "").split()))


def save_grant(tool: str, action: str) -> None:
    """Persist a grant and add it to the in-memory set."""
    key = normalize(tool, action)
    ALWAYS_ALLOWED.add(key)
    existing = list(repo.query(AlwaysAllow,
                              AlwaysAllow.tool == key[0],
                              AlwaysAllow.action == key[1]))
    if existing:
        return
    repo.add_obj(AlwaysAllow(tool=key[0], action=key[1]))


def load_grants() -> set:
    """Load all persisted grants into the in-memory set."""
    for row in repo.get_all(AlwaysAllow, limit=1000, order_desc="created_at"):
        ALWAYS_ALLOWED.add((row.tool, row.action))
    return ALWAYS_ALLOWED


def revoke_grant(tool: str, action: str) -> bool:
    """Remove a persisted grant (and the in-memory copy)."""
    key = normalize(tool, action)
    ALWAYS_ALLOWED.discard(key)
    rows = list(repo.query(AlwaysAllow, AlwaysAllow.tool == key[0],
                          AlwaysAllow.action == key[1]))
    for row in rows:
        repo.delete_by_id(AlwaysAllow, row.id)
    return bool(rows)


def list_grants() -> list:
    """All persisted grants as (tool, action) tuples, newest first."""
    rows = repo.get_all(AlwaysAllow, limit=500, order_desc="created_at")
    return [(r.tool, r.action) for r in rows]
