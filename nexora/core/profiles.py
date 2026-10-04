"""Device profiles: battery-saver / balanced / performance.

Profiles bound worker count, polling frequency, browser usage and model
context size so Nexora can run on phones (Termux), laptops and servers.
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceProfile:
    name: str
    max_workers: int
    poll_seconds: float
    allow_browser: bool
    context: int
    battery_friendly: bool


PROFILES: dict[str, DeviceProfile] = {
    "battery-saver": DeviceProfile(
        name="battery-saver", max_workers=1, poll_seconds=60.0,
        allow_browser=False, context=1024, battery_friendly=True),
    "balanced": DeviceProfile(
        name="balanced", max_workers=3, poll_seconds=15.0,
        allow_browser=True, context=4096, battery_friendly=False),
    "performance": DeviceProfile(
        name="performance", max_workers=8, poll_seconds=5.0,
        allow_browser=True, context=8192, battery_friendly=False),
}


def get_profile(name: str | None = None) -> DeviceProfile:
    """Return the named profile; unknown names fall back to balanced."""
    key = (name or os.getenv("NEXORA_PROFILE") or "balanced").strip().lower()
    return PROFILES.get(key, PROFILES["balanced"])
