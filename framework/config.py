"""Typed configuration reader.

Reads values from `config.ini` at the repository root. Environment variables
prefixed with `DJI_` override the config file (e.g., `DJI_BROWSER__HEADLESS=true`
overrides `[browser] headless`). This matters for CI where we want the same
config.ini to work both locally (headed) and in Jenkins (headless), without
code changes.
"""

from __future__ import annotations

import os
from configparser import ConfigParser
from pathlib import Path

_ENV_PREFIX = "DJI_"
_ENV_SEPARATOR = "__"  # DJI_BROWSER__HEADLESS -> [browser] headless


class ConfigReader:
    """Singleton-style reader. Caches the parsed file; env vars override on every read."""

    _config_path: Path = Path(__file__).resolve().parent.parent / "config.ini"
    _config: ConfigParser | None = None

    @classmethod
    def _load(cls) -> ConfigParser:
        if cls._config is None:
            if not cls._config_path.exists():
                raise FileNotFoundError(f"Config file not found: {cls._config_path}")
            parser = ConfigParser()
            parser.read(cls._config_path)
            cls._config = parser
        return cls._config

    @classmethod
    def _env_override(cls, section: str, key: str) -> str | None:
        env_name = f"{_ENV_PREFIX}{section.upper()}{_ENV_SEPARATOR}{key.upper()}"
        return os.environ.get(env_name)

    @classmethod
    def _require(cls, section: str, key: str) -> str:
        """Return the raw string value, preferring env var over file."""
        override = cls._env_override(section, key)
        if override is not None:
            return override

        config = cls._load()
        if not (config.has_section(section) and config.has_option(section, key)):
            raise KeyError(f"Missing config: [{section}] {key}")
        return config.get(section, key)

    @classmethod
    def read_str(cls, section: str, key: str) -> str:
        return cls._require(section, key)

    @classmethod
    def read_int(cls, section: str, key: str) -> int:
        raw = cls._require(section, key)
        try:
            return int(raw)
        except ValueError as exc:
            raise ValueError(f"[{section}] {key} is not an int: {raw!r}") from exc

    @classmethod
    def read_bool(cls, section: str, key: str) -> bool:
        raw = cls._require(section, key).strip().lower()
        if raw in {"true", "1", "yes", "on"}:
            return True
        if raw in {"false", "0", "no", "off"}:
            return False
        raise ValueError(f"[{section}] {key} is not a bool: {raw!r}")
