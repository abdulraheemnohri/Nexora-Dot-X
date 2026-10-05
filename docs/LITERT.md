# LiteRT-LM (built-in model runtime)

LiteRT-LM is Nexora's first-class local model backend. The built-in default
model is litert-community/gemma-4-E2B-it-litert-lm - a small, on-device
Gemma model in the .litertlm format (private inference, no network needed
after download).

## CLI

    nexora litert list                  # show installed .litertlm models
    nexora litert install               # download the built-in Gemma model
    nexora litert install -y            # confirm the network download explicitly
    nexora litert install -r <repo>     # any other LiteRT HF repo
    nexora litert import -y             # import into the official litert-lm registry
    nexora litert run "hello!"          # one-shot generation (Python runtime)
    nexora litert run "hi" --cli        # one-shot via the official litert-lm CLI
    nexora litert serve                 # OpenAI-compatible server on 127.0.0.1:9379
    nexora litert doctor                # runtime + model + CLI diagnostics

## Auto-attach with nexora start

    nexora start --with-litert-serve [--serve-port 9379]

starts the web server, worker AND the official litert-lm server together.
The litert-lm process is terminated cleanly when Nexora stops. If the
litert-lm CLI is not installed, Nexora warns and continues without it.

## Using serve as a model-bus provider

When 'nexora litert serve' is running, the model bus picks it up
automatically as the 'litert-serve' provider: any generation request
(chat CLI, web UI, worker tasks) is served through the OpenAI-compatible
endpoint without loading the model a second time in-process.

    NEXORA_LITERT_SERVE_URL=http://127.0.0.1:9379   # default

Loopback URLs count as on-device, so this works in local-only mode too.

## Official litert-lm CLI bridge

Nexora wraps the real LiteRT-LM command-line tool
(https://developers.google.com/edge/litert-lm/cli). If the litert-lm binary
is not on PATH, it falls back to 'uvx litert-lm'.

    nexora litert import -y -r <repo> -f <file.litertlm> -n <local-name>

maps to:

    litert-lm import --from-huggingface-repo=<repo> <file.litertlm> <local-name>

    nexora litert serve --host 127.0.0.1 --port 9379

starts the OpenAI-compatible server:

- GET /v1/models - list served models
- POST /v1/chat/completions - chat completions (streaming supported)

    curl http://localhost:9379/v1/chat/completions \\
      -H "Content-Type: application/json" \\
      -d '{"model": "gemma4-12b", "messages": [{"role": "user", "content": "Hello!"}]}'

nexora litert run accepts the official CLI options when --cli is used (or
automatically when an option needs the CLI):

- --backend cpu|gpu - GPU acceleration (Vulkan / Metal drivers)
- --mtp - Multi-Token Prediction (needs a model with a drafter)
- --attachment <file> + --vision-backend / --audio-backend
  - multimodal image/audio inputs

Examples:

    nexora litert run "Describe this" --cli --backend gpu --mtp
    nexora litert run "What is this?" --cli -a image.jpg --vision-backend gpu

## Local-only guard

Downloads and HuggingFace imports refuse to touch the network by default.
Either pass --allow-network (-y) explicitly or set NEXORA_LOCAL_ONLY=false.
Local model runs and serve need no network.

## Install path

Models land in models/litert/gemma-4-E2B-it-litert-lm.litertlm. Drop any
other .litertlm file into models/ (or models/litert/) and
nexora litert list will pick it up automatically.

## Runtime

The inference engine itself is the optional litert-lm package:

    pip install nexora-dot-x[litert]

Without it, nexora litert doctor reports the runtime as missing and the
model bus falls back to GGUF / Ollama providers.
