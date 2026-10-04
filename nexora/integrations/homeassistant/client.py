"""Optional Home Assistant integration.

Read-only by default; device control passes System 1 (ASK for state changes).
Token via NEXORA_SECRET_HA_TOKEN, URL via NEXORA_SECRET_HA_URL.
"""
import os


class HomeAssistant:
    def __init__(self):
        self.url = os.getenv("NEXORA_SECRET_HA_URL", "").rstrip("/")
        self.token = os.getenv("NEXORA_SECRET_HA_TOKEN", "")

    def configured(self) -> bool:
        return bool(self.url and self.token)

    def _client(self):
        import httpx
        return httpx.Client(base_url=self.url,
                             headers={"Authorization": "Bearer " + self.token},
                             timeout=15)

    def states(self) -> list:
        if not self.configured():
            return []
        with self._client() as c:
            return c.get("/api/states").json()

    def devices(self) -> list:
        return [s["entity_id"] for s in self.states()]

    def call_service(self, domain: str, service: str, data: dict) -> dict:
        """Service calls are high-risk: route through System 1 first."""
        from nexora.control.orchestrator import Orchestrator
        decision, approval = Orchestrator().authorize(
            "homeassistant", domain + "." + service + " " + str(data))
        if approval is not None:
            return {"ok": False, "pending_approval": approval.id}
        if decision.decision.value != "allow":
            return {"ok": False, "error": decision.reason}
        with self._client() as c:
            r = c.post("/api/services/" + domain + "/" + service, json=data)
            return {"ok": r.status_code in (200, 201), "output": r.text[:2000]}
