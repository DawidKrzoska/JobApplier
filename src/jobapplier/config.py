"""Application configuration loading utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


class JobSourceConfig(BaseModel):
    """Configuration describing a job-source adapter instance."""

    type: str
    options: Dict[str, Any] = Field(default_factory=dict)


class NotificationConfig(BaseModel):
    """Notification channel configuration."""

    channel: str = "cli"
    options: Dict[str, Any] = Field(default_factory=dict)


class StorageConfig(BaseModel):
    """State persistence configuration."""

    path: Path = Path(".jobapplier-state.json")


class AppConfig(BaseModel):
    """Top-level validated config."""

    job_sources: List[JobSourceConfig]
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    scoring: Dict[str, Any] = Field(default_factory=dict)
    approvals: Dict[str, Any] = Field(default_factory=dict)


def load_config(path: Path | str) -> AppConfig:
    """Read a YAML config file and return a validated `AppConfig`."""

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text()) or {}
    raw = _expand_env(raw)
    try:
        return AppConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration: {exc}") from exc


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(val) for key, val in value.items()}
    return value
