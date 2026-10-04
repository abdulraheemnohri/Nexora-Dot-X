"""Memory federation: resolve conflicts across memory stores.

Stores: user, project, bot, shared. Priority: manual > trusted source >
highest confidence > newest. Never silently overwrites important memory.
"""
from dataclasses import dataclass


@dataclass
class MemoryItem:
    store: str          # user / project / bot / shared
    content: str
    confidence: float = 1.0
    created_at: float = 0.0
    trusted: bool = False
    approved: bool = False


class Federation:
    """Pick the winning record when stores disagree."""

    def resolve(self, items) -> MemoryItem | None:
        items = [i for i in items if i is not None]
        if not items:
            return None
        # manual approval beats everything
        approved = [i for i in items if i.approved]
        if approved:
            items = approved
        # trusted sources next
        trusted = [i for i in items if i.trusted]
        if trusted:
            items = trusted
        # then confidence, then recency
        items.sort(key=lambda i: (i.confidence, i.created_at), reverse=True)
        return items[0]

    def merge(self, items) -> str:
        """Merge strategy: dedupe + concatenate distinct contents."""
        seen = set()
        parts = []
        for i in sorted(items, key=lambda x: x.created_at, reverse=True):
            key = i.content.strip().lower()
            if key not in seen:
                seen.add(key)
                parts.append(i.content.strip())
        return "\n".join(parts)
