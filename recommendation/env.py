from __future__ import annotations

import os


class MissingEnvError(RuntimeError):
    """Raised when a required environment variable is missing or blank."""


def require_env(name: str) -> str:
    """Return a non-empty, stripped environment variable value."""
    value = os.getenv(name)
    if not value or not value.strip():
        raise MissingEnvError(f"{name} is not set.")
    return value.strip()
