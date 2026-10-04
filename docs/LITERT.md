# LiteRT-LM

LiteRT-LM is the built-in, first-class local runtime.

- Models are .litertlm files under NEXORA_LITERT_DIR (default models/litert/)
- Any compatible model works via its manifest (Gemma, Qwen, FunctionGemma, ...)
- The runtime package is optional: pip install nexora-dot-x[litert]
- Without the package, Nexora stays fully functional; generation is simply
  unavailable and diagnostics explain exactly why.

CLI:

    nexora litert scan      # list found .litertlm files
    nexora litert list
    nexora litert doctor    # runtime / directory / model / inference checks

The provider exposes the common Model Bus interface: load, unload, generate,
stream, health, metadata, context_info.
