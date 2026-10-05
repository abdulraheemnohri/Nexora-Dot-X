from nexora.browser.manager import BrowserPolicy


def test_browser_domain_allowlist():
    p = BrowserPolicy(["example.com"])
    assert p.allows("https://example.com/page")
    assert p.allows("https://sub.example.com")
    assert not p.allows("https://evil-example.com")
    assert not p.allows("https://example.org")
