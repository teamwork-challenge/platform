import json
import os
from pathlib import Path
from typing import Any
import warnings


class ConfigManager:
    """Manager for handling configuration storage and retrieval."""

    def __init__(self, config_path: Path):
        """Initialize the ConfigManager."""
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Any:
        """Load configuration from the file."""
        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            warnings.warn(f"Config file '{self.config_path}' is corrupted or not valid JSON: {e}. Using defaults.")
            return {}
        except FileNotFoundError:
            # Race condition: file disappeared after exists() check
            return {}

    def save_config(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self._config, f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
        self.save_config()

    def remove(self, key: str) -> None:
        """Remove a configuration value."""
        if key in self._config:
            del self._config[key]
            self.save_config()

    def get_api_key(self) -> str | None:
        """Get an API key from config."""
        res = self.get("api_key")
        return str(res) if res else None

    def save_api_key(self, api_key: str) -> None:
        """Save an API key to config."""
        self.set("api_key", api_key)

    def remove_api_key(self) -> None:
        """Remove an API key from config."""
        self.remove("api_key")

    def get_base_url(self) -> str:
        """Get base URL from a config or environment variable."""
        return self.get("base_url") or os.environ.get("CHALLENGE_API_URL", "http://127.0.0.1:8088")

    def save_base_url(self, base_url: str) -> None:
        """Save base URL to config."""
        self.set("base_url", base_url)