"""HTTP tool, constrained by the network policy (offline by default)."""
import os

from nexora.tools.registry import ToolSpec


class HttpTool:
    id = "http"

    def run(self, action: str) -> dict:
        # env checked at call time so config reloads / test patches apply
        if os.getenv("NEXORA_LOCAL_ONLY", "true").lower() == "true":
            return {"ok": False,
                    "output": "network disabled: NEXORA_LOCAL_ONLY=true"}
        import httpx
        try:
            r = httpx.get(action.strip(), timeout=30, follow_redirects=True)
            content_type = r.headers.get("content-type", "")
            if "html" in content_type:
                import re
                text = re.sub(r"<[^>]+>", " ", r.text)
                return {"ok": True, "output": " ".join(text.split())[:20000]}
            return {"ok": True, "output": r.text[:20000]}
        except Exception as e:
            return {"ok": False, "output": "http error: " + str(e)}


def register(registry) -> ToolSpec:
    spec = ToolSpec("http", "HTTP", "Fetch URLs (disabled in local-only mode).", risk="medium")
    registry.register(spec, HttpTool().run)
    return spec
