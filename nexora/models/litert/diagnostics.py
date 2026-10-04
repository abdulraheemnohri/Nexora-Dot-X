"""LiteRT-LM discovery and diagnostics (no network required)."""
from pathlib import Path
from nexora.config import settings
from nexora.models.litert.manifest import load_manifest


def scan(model_dir: str | Path | None = None) -> dict:
    directory = Path(model_dir) if model_dir else settings.litert_dir
    models = []
    if directory.exists():
        for p in sorted(directory.glob("**/*.litertlm")):
            m = load_manifest(p)
            if m:
                models.append({"path": str(p), "name": m.name,
                               "family": m.family, "size": m.size_bytes,
                               "context": m.context})
    return {"runtime_available": runtime_available(),
            "directory": str(directory),
            "models": models}


def runtime_available() -> bool:
    try:
        import litert_lm  # noqa: F401
        return True
    except ImportError:
        return False


def doctor() -> list:
    checks = []
    info = scan()
    checks.append(("LiteRT runtime package",
                   "PASS" if info["runtime_available"]
                   else "WARN: install with 'pip install nexora-dot-x[litert]'"))
    checks.append(("Model directory", f"PASS: {info['directory']}"
                   if Path(info["directory"]).exists() else "FAIL: missing"))
    checks.append((".litertlm models",
                   f"PASS: {len(info['models'])} found" if info["models"]
                   else "WARN: no models installed yet"))
    return checks
