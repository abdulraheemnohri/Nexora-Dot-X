from nexora.core.profiles import get_profile, PROFILES


def test_default_is_balanced():
    assert get_profile("nope").name == "balanced"


def test_battery_saver_limits():
    p = get_profile("battery-saver")
    assert p.max_workers == 1
    assert p.allow_browser is False
    assert p.context <= 2048


def test_performance_expands():
    p = get_profile("performance")
    assert p.max_workers > 4
    assert p.poll_seconds <= 5


def test_all_profiles_present():
    assert set(PROFILES) == {"battery-saver", "balanced", "performance"}
