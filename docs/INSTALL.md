# Installation

## Linux / macOS / Termux

    pkg update && pkg install python git clang   # Termux only
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .

## Windows

    py -m venv .venv
    .venv\Scripts\activate
    pip install -e .

## Optional extras

    pip install -e ".[litert]"     # LiteRT-LM runtime
    pip install -e ".[browser]"     # Playwright
    pip install -e ".[vector]"     # FAISS memory index
    pip install -e ".[dev]"         # pytest + ruff

## Configuration (.env)

    NEXORA_HOST=127.0.0.1
    NEXORA_PORT=8000
    NEXORA_DATA_DIR=./data
    NEXORA_MODEL_DIR=./models
    NEXORA_LOCAL_ONLY=true
    NEXORA_AUTH_ENABLED=false
    NEXORA_LOG_LEVEL=INFO

## First start

    nexora doctor
    nexora start
