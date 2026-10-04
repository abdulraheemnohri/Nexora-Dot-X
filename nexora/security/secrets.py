"""Secrets: environment-backed store. Never persisted in plain memory/DB."""
import os


class SecretsStore:
    PREFIX = "NEXORA_SECRET_"

    @classmethod
    def set_env(cls, name: str, value: str):
        os.environ[cls.PREFIX + name.upper()] = value

    @classmethod
    def get(cls, name: str) -> str | None:
        return os.getenv(cls.PREFIX + name.upper())

    @classmethod
    def mask(cls, value: str) -> str:
        if not value:
            return ""
        if len(value) <= 4:
            return "*" * len(value)
        return value[:2] + "*" * (len(value) - 4) + value[-2:]

    @classmethod
    def names(cls) -> list:
        return [k[len(cls.PREFIX):].lower() for k in os.environ if k.startswith(cls.PREFIX)]
