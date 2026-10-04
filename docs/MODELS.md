# Model Management

Backends (priority order): LiteRT-LM -> GGUF -> Ollama -> remote (only when
`NEXORA_LOCAL_ONLY=false`).

## UI
- `/models` — live health table per backend + LiteRT scan button
- `POST /api/models/scan` — rescans the model directory

## Install a model
```bash
nexora litert scan          # find LiteRT-LM models
# or drop .gguf files in ./models
ollama pull llama3          # Ollama backend
```

No model ready => chat returns an honest install hint, never a fake reply.
