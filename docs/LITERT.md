# LiteRT-LM (built-in model runtime)

LiteRT-LM is Nexora's first-class local model backend. The built-in default
model is **litert-community/gemma-4-E2B-it-litert-lm** - a small, on-device
Gemma model in the .litertlm format (private inference, no network needed
after download).

## CLI

    nexora litert list                  # show installed .litertlm models
    nexora litert install               # download the built-in Gemma model
    nexora litert install -y            # confirm the network download explicitly
    nexora litert install -r <repo>     # any other LiteRT HF repo
    nexora litert run "hello!"          # one-shot generation with the built-in model
    nexora litert doctor                # runtime + model diagnostics

## Local-only guard

Downloads refuse to touch the network by default. Either pass
`--allow-network` explicitly or set `NEXORA_LOCAL_ONLY=false`. Already
downloaded models never re-download.

## Install path

Models land in `models/litert/gemma-4-E2B-it-litert-lm.litertlm`. Drop any
other `.litertlm` file into `models/` (or `models/litert/`) and
`nexora litert list` will pick it up automatically.

## Runtime

The inference engine itself is the optional `litert-lm` package:

    pip install nexora-dot-x[litert]

Without it, `nexora litert doctor` reports the runtime as missing and the
model bus falls back to GGUF / Ollama providers.
