"""Dot lifecycle manager backed by SQLite."""
from nexora.database.models import Dot
from nexora.database import repositories as repo
from nexora.bots.templates import TEMPLATES
from nexora.config import settings


class BotManager:
    def list(self) -> list:
        return repo.get_all(Dot, limit=500, order_desc="created_at")

    def get(self, dot_id: str):
        return repo.get_by_id(Dot, dot_id)

    def create(self, name: str, mission: str = "", description: str = "",
               personality: str = "", system_prompt: str = "",
               model: str = "litert", template: str = "custom",
               workspace: str = "") -> Dot:
        ws = workspace or name.lower().replace(" ", "-")
        (settings.workspace_dir / ws).mkdir(parents=True, exist_ok=True)
        d = Dot(name=name, mission=mission, description=description,
                personality=personality, system_prompt=system_prompt,
                model=model, template=template, workspace=ws)
        return repo.add_obj(d)

    def create_from_template(self, key: str) -> Dot:
        t = TEMPLATES.get(key)
        if not t:
            raise ValueError(f"unknown template: {key}")
        return self.create(name=t["name"], mission=t["mission"],
                           personality=t["personality"], template=key)

    def duplicate(self, dot_id: str) -> Dot | None:
        d = repo.get_by_id(Dot, dot_id)
        if d is None:
            return None
        return self.create(name=f"{d.name} (copy)", mission=d.mission,
                           description=d.description, personality=d.personality,
                           system_prompt=d.system_prompt, model=d.model,
                           template=d.template)

    def set_status(self, dot_id: str, status: str):
        d = repo.get_by_id(Dot, dot_id)
        if d:
            return repo.update_fields(d, status=status)
        return None

    def start(self, dot_id: str):
        return self.set_status(dot_id, "online")

    def pause(self, dot_id: str):
        return self.set_status(dot_id, "paused")

    def stop(self, dot_id: str):
        return self.set_status(dot_id, "offline")

    def archive(self, dot_id: str):
        d = repo.get_by_id(Dot, dot_id)
        if d:
            return repo.update_fields(d, enabled=False, status="offline")
        return None

    def delete(self, dot_id: str) -> bool:
        return repo.delete_by_id(Dot, dot_id)
