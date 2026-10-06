"""Dot lifecycle and configuration service."""
import json
from nexora.database.models import Dot
from nexora.database import repositories as repo

TEMPLATES = {
    "research": {"mission": "Research and synthesize information.", "personality": "Careful, evidence-driven.", "template": "research"},
    "coding": {"mission": "Build, test, debug and maintain software.", "personality": "Precise, test-first.", "template": "coding"},
    "devops": {"mission": "Operate and automate infrastructure safely.", "personality": "Conservative, observable.", "template": "devops"},
    "writer": {"mission": "Draft and refine high-quality content.", "personality": "Clear and structured.", "template": "writer"},
    "security": {"mission": "Analyze systems defensively.", "personality": "Risk-aware and cautious.", "template": "security"},
    "data": {"mission": "Analyze and transform data.", "personality": "Quantitative and reproducible.", "template": "data"},
    "browser": {"mission": "Perform approved browser workflows.", "personality": "Careful and state-aware.", "template": "browser"},
    "personal": {"mission": "Assist with personal workflows.", "personality": "Helpful and concise.", "template": "personal"},
}


class DotService:
    def create(self, name: str, *, template: str = "custom", mission: str = "",
               personality: str = "", workspace: str = "", model: str = "litert",
               system_prompt: str = ""):
        preset = TEMPLATES.get(template, {})
        return repo.add_obj(Dot(
            name=name,
            template=template,
            mission=mission or preset.get("mission", ""),
            personality=personality or preset.get("personality", ""),
            workspace=workspace,
            model=model,
            system_prompt=system_prompt,
            status="offline",
            enabled=True,
        ))

    def get(self, dot_id: str):
        return repo.get_by_id(Dot, dot_id)

    def list(self, enabled: bool | None = None):
        if enabled is None:
            return repo.get_all(Dot, order_desc="created_at")
        return repo.query(Dot, Dot.enabled == enabled, limit=1000)

    def update(self, dot_id: str, **fields):
        allowed = {
            "name", "description", "mission", "personality", "system_prompt",
            "model", "template", "status", "enabled", "workspace"
        }
        return repo.update_fields(
            repo.get_by_id(Dot, dot_id),
            **{k: v for k, v in fields.items() if k in allowed}
        )

    def pause(self, dot_id: str):
        return self.update(dot_id, enabled=False, status="paused")

    def resume(self, dot_id: str):
        return self.update(dot_id, enabled=True, status="offline")

    def export(self, dot_id: str) -> dict | None:
        d = self.get(dot_id)
        if not d:
            return None
        return {k: getattr(d, k) for k in [
            "id", "name", "description", "mission", "personality",
            "system_prompt", "model", "template", "status", "enabled",
            "workspace", "created_at"
        ]}

    def import_config(self, data: dict):
        allowed = {k: data.get(k) for k in [
            "name", "description", "mission", "personality",
            "system_prompt", "model", "template", "workspace"
        ] if data.get(k) is not None}
        return self.create(**allowed)
