import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigManager:
    """Manager for handling configuration storage and retrieval."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the ConfigManager.

        Args:
            config_path: Path to the config file. If not provided, uses ~/.challenge/config.json.
        """
        self.config_path = config_path or Path.home() / ".challenge" / "config.json"
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_config(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self._config, f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
        self.save_config()

    def remove(self, key: str) -> None:
        """Remove a configuration value.

        Args:
            key: Configuration key
        """
        if key in self._config:
            del self._config[key]
            self.save_config()

    def get_api_key(self) -> Optional[str]:
        """Get API key from config."""
        return self.get("api_key")

    def save_api_key(self, api_key: str) -> None:
        """Save API key to config."""
        self.set("api_key", api_key)

    def remove_api_key(self) -> None:
        """Remove API key from config."""
        self.remove("api_key")

    def get_base_url(self) -> str:
        """Get base URL from config or environment variable."""
        return self.get("base_url") or os.environ.get("CHALLENGE_API_URL", "http://127.0.0.1:8088")



    def save_base_url(self, base_url: str) -> None:
        """Save base URL to config."""
        self.set("base_url", base_url)