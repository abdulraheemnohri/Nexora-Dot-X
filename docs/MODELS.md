# Model System

The Model Bus routes across providers with the failover order:

    LiteRT-LM -> GGUF (llama.cpp) -> Ollama -> remote (optional)

## Providers
- **LiteRT-LM** (built-in): .litertlm files, optional runtime package.
- **GGUF**: works with a local llama.cpp server (127.0.0.1:8080) or llama-cpp-python.
- **Ollama**: local Ollama daemon on 127.0.0.1:11434.
- **OpenAI-compatible remote**: only when NEXORA_LOCAL_ONLY=false and configured.

All providers implement: load, unload, generate, stream, health, metadata, context_info.
Check readiness: nexora doctor
