"""Browser automation via Playwright (optional dependency).

Every action is still routed through System 1 policy by the executor.
"""
from nexora.control.policy import PolicyEngine, Decision
from nexora.control.audit import audit


class BrowserManager:
    def __init__(self):
        self.policy = PolicyEngine()
        self._pw = None
        self._browser = None
        self._page = None

    def available(self) -> bool:
        try:
            import playwright  # noqa: F401
            return True
        except ImportError:
            return False

    def _ensure(self, headless: bool = True):
        if self._page is not None:
            return self._page
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=headless)
        self._page = self._browser.new_page()
        return self._page

    def run(self, action: str) -> dict:
        decision = self.policy.evaluate("browser", action)
        audit("agent", tool="browser", action=action,
              decision=decision.decision.value, outcome=decision.reason)
        if decision.decision is Decision.BLOCK:
            return {"ok": False, "output": f"BLOCKED: {decision.reason}"}
        if decision.decision is Decision.ASK:
            return {"ok": False, "output": "APPROVAL_REQUIRED", "approval_needed": True}
        if not self.available():
            return {"ok": False,
                    "output": "Playwright not installed: pip install nexora-dot-x[browser] && playwright install chromium"}
        try:
            page = self._ensure()
            op, _, arg = action.partition("|")
            op = op.strip().lower()
            if op == "goto":
                page.goto(arg.strip())
                return {"ok": True, "output": page.title()}
            if op == "text":
                return {"ok": True, "output": page.inner_text("body")[:20000]}
            if op == "screenshot":
                path = arg.strip() or "screenshot.png"
                page.screenshot(path=path)
                return {"ok": True, "output": f"saved {path}"}
            if op == "click":
                page.click(arg.strip())
                return {"ok": True, "output": "clicked"}
            if op == "type":
                sel, _, text = arg.partition("|")
                page.fill(sel.strip(), text)
                return {"ok": True, "output": "typed"}
            return {"ok": False, "output": f"unsupported browser op: {op}"}
        except Exception as e:
            return {"ok": False, "output": f"browser error: {e}"}

    def close(self):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
        self._browser = self._page = self._pw = None
