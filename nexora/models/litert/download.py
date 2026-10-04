"""Model downloads for LiteRT-LM.

Local-only policy: network downloads require an explicit --allow-network /
allow_network=True from the user (or NEXORA_LOCAL_ONLY=false). The built-in
default model is litert-community/gemma-4-E2B-it-litert-lm.
"""
from pathlib import Path
import urllib.request

DEFAULT_MODEL_REPO = "litert-community/gemma-4-E2B-it-litert-lm"
DEFAULT_MODEL_FILE = "model.litertlm"
HF_URL = "https://huggingface.co/{repo}/resolve/main/{file}"


def _allow_network(allow_network) -> bool:
    import os
    if allow_network:
        return True
    return os.getenv("NEXORA_LOCAL_ONLY", "true").lower() != "true"


def download(url, destination, allow_network=False):
    """Stream a URL to disk. Refuses to touch the network in local-only mode."""
    if not _allow_network(allow_network):
        raise PermissionError(
            "Network model downloads are disabled by local-only policy "
            "(pass allow_network=True or set NEXORA_LOCAL_ONLY=false)")
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as src, dest.open("wb") as out:
        while chunk := src.read(1024 * 1024):
            out.write(chunk)
    return str(dest)


def download_default_model(model_dir, allow_network=False,
                           repo=DEFAULT_MODEL_REPO, file=DEFAULT_MODEL_FILE):
    """Download the built-in Gemma model into the LiteRT model dir."""
    url = HF_URL.format(repo=repo, file=file)
    name = repo.split("/")[-1]
    dest = Path(model_dir) / "litert" / (name + ".litertlm")
    if dest.exists() and dest.stat().st_size > 0:
        return {"ok": True, "path": str(dest), "cached": True}
    path = download(url, dest, allow_network=allow_network)
    return {"ok": True, "path": path, "cached": False}


def ensure_default_model(model_dir, allow_network=False):
    """Return path to the built-in model, downloading only if missing."""
    name = DEFAULT_MODEL_REPO.split("/")[-1]
    dest = Path(model_dir) / "litert" / (name + ".litertlm")
    if dest.exists() and dest.stat().st_size > 0:
        return {"ok": True, "path": str(dest), "cached": True}
    return download_default_model(model_dir, allow_network=allow_network)
