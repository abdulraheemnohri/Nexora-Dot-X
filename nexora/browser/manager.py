"""Async Playwright browser control.

Browser sessions are process-local and are exposed only through System 1.
Domain allowlisting is enforced before navigation.
"""
from dataclasses import dataclass, field
from urllib.parse import urlparse
from nexora.control.audit import audit


@dataclass
class BrowserPolicy:
    allowed_domains: list[str] = field(default_factory=list)

    def allows(self, url: str) -> bool:
        host = (urlparse(url).hostname or "").lower().rstrip(".")
        return any(host == d.lower().lstrip("*.").rstrip(".") or
                   host.endswith("." + d.lower().lstrip("*.").rstrip("."))
                   for d in self.allowed_domains)


@dataclass
class BrowserSession:
    session_id: str
    headless: bool = True
    page: object | None = None


class BrowserManager:
    def __init__(self, policy: BrowserPolicy | None = None):
        self.policy = policy or BrowserPolicy([])
        self._playwright = None
        self._browser = None
        self._sessions: dict[str, BrowserSession] = {}

    def available(self) -> bool:
        try:
            import playwright.async_api  # noqa: F401
            return True
        except ImportError:
            return False

    async def _ensure_runtime(self):
        if self._playwright is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

    async def create(self, session_id: str, headless: bool = True) -> BrowserSession:
        if not session_id.strip():
            raise ValueError("session_id cannot be empty")
        if session_id in self._sessions:
            return self._sessions[session_id]
        if not self.available():
            raise RuntimeError("Playwright not installed; install the browser extra and Chromium")
        from playwright.async_api import async_playwright
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        self._browser = self._browser or await self._playwright.chromium.launch(headless=headless)
        page = await self._browser.new_page()
        session = BrowserSession(session_id, headless, page)
        self._sessions[session_id] = session
        return session

    def _get(self, session_id: str):
        session = self._sessions.get(session_id)
        if session is None or session.page is None:
            raise ValueError("browser session not found")
        return session

    async def navigate(self, session_id: str, url: str):
        if not self.policy.allows(url):
            audit("agent", tool="browser.navigate", action=url, decision="BLOCK", outcome="domain not allowlisted")
            return {"ok": False, "output": "BLOCKED: domain is not allowlisted"}
        session = self._get(session_id)
        await session.page.goto(url, wait_until="domcontentloaded")
        return {"ok": True, "output": await session.page.title()}

    async def screenshot(self, session_id: str, path: str):
        session = self._get(session_id)
        await session.page.screenshot(path=path)
        return {"ok": True, "output": f"saved {path}"}

    async def content(self, session_id: str):
        session = self._get(session_id)
        return {"ok": True, "output": (await session.page.content())[:20000]}

    async def close(self, session_id: str):
        session = self._get(session_id)
        await session.page.close()
        self._sessions.pop(session_id, None)
        return {"ok": True, "output": "closed"}

    async def close_all(self):
        for session_id in list(self._sessions):
            try:
                await self.close(session_id)
            except Exception:
                pass
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = self._playwright = None
