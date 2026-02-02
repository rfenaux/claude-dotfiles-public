"""
CTM Configuration Management

Handles loading, validation, and access to CTM configuration.
Supports both global (~/.claude/ctm/config.json) and project-level
(.claude/ctm/config.json) configuration with inheritance.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Default configuration values
DEFAULTS = {
    "version": "2.0.0",
    "memory_tiers": {
        "enabled": True,
        "l1_max_agents": 2,
        "l1_token_budget": 4000,
        "l2_max_agents": 5,
        "l2_token_budget": 8000,
        "l3_retention_days": 30,
        "pressure_threshold": 0.7,
        "compression_model": "haiku",
        "auto_manage": True
    },
    "self_management": {
        "enabled": True,
        "pressure_threshold": 0.7,
        "auto_summarize": True,
        "summarize_model": "haiku",
        "verbose_logging": False
    },
    "working_memory": {
        "max_hot_agents": 5,
        "token_budget": 8000,
        "eviction_policy": "weighted_lru",
        "decay_rate": 0.1
    },
    "priority": {
        "weights": {
            "urgency": 0.25,
            "recency": 0.20,
            "value": 0.20,
            "novelty": 0.15,
            "user_signal": 0.15,
            "error_boost": 0.05
        },
        "recency_halflife_hours": 24,
        "min_priority_threshold": 0.1
    },
    "checkpointing": {
        "micro_interval_tools": 5,
        "standard_interval_minutes": 5,
        "full_on_eviction": True,
        "session_end_mandatory": True
    },
    "consolidation": {
        "auto_extract_decisions": True,
        "briefing_max_tokens": 500,
        "stale_agent_days": 30
    },
    "triggers": {
        "keyword_patterns": [
            "back to {agent}",
            "continue {agent}",
            "what about {agent}",
            "resume {agent}",
            "switch to {agent}"
        ],
        "time_based": {
            "enabled": False,
            "reminder_after_hours": 48
        }
    },
    "ui": {
        "status_bar_enabled": True,
        "briefing_on_start": True,
        "show_priority_scores": False
    },
    "logging": {
        "level": "INFO",
        "max_log_size_mb": 10,
        "retention_days": 30
    }
}


@dataclass
class CTMConfig:
    """Configuration container with typed access."""

    _data: dict = field(default_factory=dict)
    _global_path: Path = field(default_factory=lambda: Path.home() / ".claude" / "ctm" / "config.json")
    _project_path: Optional[Path] = None

    def __post_init__(self):
        self._data = self._load_merged_config()

    def _load_merged_config(self) -> dict:
        """Load and merge global + project config."""
        config = DEFAULTS.copy()

        # Load global config
        if self._global_path.exists():
            with open(self._global_path, 'r') as f:
                global_config = json.load(f)
                config = self._deep_merge(config, global_config)

        # Load project config if exists
        if self._project_path and self._project_path.exists():
            with open(self._project_path, 'r') as f:
                project_config = json.load(f)
                config = self._deep_merge(config, project_config)

        return config

    def _deep_merge(self, base: dict, overlay: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, path: str, default: Any = None) -> Any:
        """Get config value by dot-notation path."""
        keys = path.split('.')
        value = self._data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, path: str, value: Any, persist: bool = True) -> None:
        """Set config value and optionally persist to file."""
        keys = path.split('.')
        data = self._data
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value

        if persist:
            self.save()

    def save(self) -> None:
        """Save current config to global config file."""
        self._global_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._global_path, 'w') as f:
            json.dump(self._data, f, indent=2)

    # Convenience properties
    @property
    def max_hot_agents(self) -> int:
        return self.get('working_memory.max_hot_agents', 5)

    @property
    def token_budget(self) -> int:
        return self.get('working_memory.token_budget', 8000)

    @property
    def priority_weights(self) -> dict:
        return self.get('priority.weights', DEFAULTS['priority']['weights'])

    @property
    def recency_halflife_hours(self) -> float:
        return self.get('priority.recency_halflife_hours', 24)

    @property
    def briefing_on_start(self) -> bool:
        return self.get('ui.briefing_on_start', True)

    @property
    def raw(self) -> dict:
        """Get raw configuration dictionary."""
        return self._data

    # Memory tier properties
    @property
    def memory_tiers_enabled(self) -> bool:
        return self.get('memory_tiers.enabled', True)

    @property
    def pressure_threshold(self) -> float:
        return self.get('memory_tiers.pressure_threshold', 0.7)

    @property
    def l1_max_agents(self) -> int:
        return self.get('memory_tiers.l1_max_agents', 2)

    @property
    def l2_max_agents(self) -> int:
        return self.get('memory_tiers.l2_max_agents', 5)

    @property
    def auto_manage_memory(self) -> bool:
        return self.get('self_management.enabled', True)


def get_ctm_dir() -> Path:
    """Get the global CTM directory path."""
    return Path.home() / ".claude" / "ctm"


def get_project_ctm_dir(project_path: Optional[Path] = None) -> Optional[Path]:
    """Get project-level CTM directory if it exists."""
    if project_path is None:
        project_path = Path.cwd()

    ctm_dir = project_path / ".claude" / "ctm"
    return ctm_dir if ctm_dir.exists() else None


def load_config(project_path: Optional[Path] = None) -> CTMConfig:
    """Load CTM configuration with optional project override."""
    project_config_path = None
    if project_path:
        project_ctm = get_project_ctm_dir(project_path)
        if project_ctm:
            project_config_path = project_ctm / "config.json"

    return CTMConfig(_project_path=project_config_path)
