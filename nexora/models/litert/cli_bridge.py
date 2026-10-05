"""Bridge to the official litert-lm CLI.

Wraps the real LiteRT-LM command-line tool (see
https://developers.google.com/edge/litert-lm/cli): model import from
HuggingFace, one-shot prompt runs with GPU / Multi-Token-Prediction /
attachment options, and the OpenAI-compatible local server (port 9379).
"""
import shutil
import subprocess

from nexora.models.litert.download import _allow_network

NOT_FOUND_HINT = (
    "litert-lm CLI not found. Install it with 'pip install litert-lm' "
    "(or 'uv tool install litert-lm', or run via 'uvx litert-lm')."
)


def resolve_cli():
    """Return the command prefix for the litert-lm CLI, or None if absent."""
    if shutil.which("litert-lm"):
        return ["litert-lm"]
    if shutil.which("uvx"):
        return ["uvx", "litert-lm"]
    return None


def require_network(allow_network):
    """Local-only guard for litert-lm operations that need the network."""
    if not _allow_network(allow_network):
        raise PermissionError(
            "litert-lm network operation blocked by local-only policy "
            "(pass --allow-network or set NEXORA_LOCAL_ONLY=false)")


def build_import_args(repo, filename, name):
    """Args for litert-lm import --from-huggingface-repo=... file name."""
    return ["import", "--from-huggingface-repo=" + repo, filename, name]


def build_serve_args(host="127.0.0.1", port=9379, verbose=False):
    """Args for litert-lm serve (OpenAI-compatible server)."""
    args = ["serve", "--host=" + host, "--port=" + str(port)]
    if verbose:
        args.append("--verbose")
    return args


def build_run_args(model_ref, prompt=None, backend=None,
                   speculative=False, attachment=None,
                   vision_backend=None, audio_backend=None, from_repo=None):
    """Args for litert-lm run <ref> [options].

    With from_repo set, model_ref is the .litertlm filename from that
    HuggingFace repo (network import); otherwise it is a local path/name.
    """
    args = ["run"]
    if from_repo:
        args.append("--from-huggingface-repo=" + from_repo)
    args.append(model_ref)
    if backend:
        args.append("--backend=" + backend)
    if speculative:
        args.append("--enable-speculative-decoding=true")
    if vision_backend:
        args.append("--vision-backend=" + vision_backend)
    if audio_backend:
        args.append("--audio-backend=" + audio_backend)
    if attachment:
        args.append("--attachment=" + attachment)
    if prompt is not None:
        args.append("--prompt=" + prompt)
    return args


def run_cli(args, network=False):
    """Run a litert-lm command and return the completed process.

    network=True means the operation may contact HuggingFace; the local-only
    guard is checked by the caller (which knows the user's intent).
    """
    prefix = resolve_cli()
    if prefix is None:
        raise RuntimeError(NOT_FOUND_HINT)
    return subprocess.run(prefix + args, check=False, capture_output=True,
                          text=True)


def serve_cli(args):
    """Run litert-lm serve in the foreground (streams logs to the user)."""
    prefix = resolve_cli()
    if prefix is None:
        raise RuntimeError(NOT_FOUND_HINT)
    return subprocess.call(prefix + args)


def spawn_serve(args):
    """Start litert-lm serve in the background; return the Popen or None."""
    prefix = resolve_cli()
    if prefix is None:
        return None
    return subprocess.Popen(prefix + args)
