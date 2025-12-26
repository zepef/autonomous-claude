"""
Configuration loader for AI-Defender

Loads settings from YAML and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Config file path
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


def _resolve_env_vars(config: Dict) -> Dict:
    """Recursively resolve ${VAR} placeholders with environment variables"""
    resolved = {}
    for key, value in config.items():
        if isinstance(value, dict):
            resolved[key] = _resolve_env_vars(value)
        elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            resolved[key] = os.environ.get(env_var, "")
        else:
            resolved[key] = value
    return resolved


def load_config(config_path: Path = CONFIG_PATH) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Resolve environment variables
    config = _resolve_env_vars(config)

    return config


class Config:
    """Configuration singleton"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = load_config()
        return cls._instance

    def __getattr__(self, name: str) -> Any:
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"Config has no attribute '{name}'")

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with optional default"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @property
    def as_dict(self) -> Dict:
        """Return full config as dictionary"""
        return self._config.copy()


# Convenience function
def get_config() -> Config:
    """Get the configuration singleton"""
    return Config()


if __name__ == "__main__":
    # Test loading config
    from pprint import pprint

    config = get_config()
    print("Configuration loaded:")
    pprint(config.as_dict)

    print("\nAccessing nested values:")
    print(f"  API Model: {config.get('api.model')}")
    print(f"  Evolution Population: {config.get('evolution.population_size')}")
    print(f"  Honeypot Port: {config.get('honeypot.port')}")
