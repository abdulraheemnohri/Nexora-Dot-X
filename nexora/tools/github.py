"""GitHub tool: repository inspection via the GitHub API.

Credentials come from NEXORA_SECRET_GITHUB_TOKEN; never stored in memory.
"""
import os
from nexora.tools.registry import ToolSpec


class GitHubTool:
    id = "github"

    def _headers(self) -> dict | None:
        token = os.getenv("NEXORA_SECRET_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
        return {"Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"} if token else None

    def run(self, action: str) -> dict:
        import httpx
        headers = self._headers()
        if headers is None:
            return {"ok": False,
                    "output": "no GitHub token configured (NEXORA_SECRET_GITHUB_TOKEN)"}
        op, _, arg = action.partition("|")
        op = op.strip().lower()
        try:
            if op == "repo":
                owner, _, repo = arg.strip().partition("/")
                r = httpx.get(f"https://api.github.com/repos/{owner}/{repo}",
                              headers=headers, timeout=30)
                r.raise_for_status()
                d = r.json()
                return {"ok": True, "output": f"{d['full_name']}: {d['description']} "
                        f"(stars {d['stargazers_count']}, default branch {d['default_branch']})"}
            if op == "issues":
                owner, _, repo = arg.strip().partition("/")
                r = httpx.get(f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page=10",
                              headers=headers, timeout=30)
                r.raise_for_status()
                return {"ok": True, "output": "\n".join(
                    f"#{i['number']} {i['title']}" for i in r.json()) or "no open issues"}
            if op == "branches":
                owner, _, repo = arg.strip().partition("/")
                r = httpx.get(f"https://api.github.com/repos/{owner}/{repo}/branches",
                              headers=headers, timeout=30)
                r.raise_for_status()
                return {"ok": True, "output": ", ".join(b["name"] for b in r.json())}
            return {"ok": False, "output": f"unsupported github op: {op}"}
        except Exception as e:
            return {"ok": False, "output": f"github error: {e}"}


def register(registry) -> ToolSpec:
    spec = ToolSpec("github", "GitHub", "GitHub repo/issues/branches via API (token-gated).", risk="medium")
    registry.register(spec, GitHubTool().run)
    return spec
