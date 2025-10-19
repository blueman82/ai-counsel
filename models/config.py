"""Configuration loading and validation."""
from pathlib import Path
import os
import re
import warnings
import yaml
from typing import Literal, Union, Optional, Annotated
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv


class CLIAdapterConfig(BaseModel):
    """Configuration for CLI-based adapter."""

    type: Literal["cli"] = "cli"
    command: str
    args: list[str]
    timeout: int = 60


class HTTPAdapterConfig(BaseModel):
    """Configuration for HTTP-based adapter."""

    type: Literal["http"] = "http"
    base_url: str
    api_key: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    timeout: int = 60
    max_retries: int = 3

    @field_validator("api_key", "base_url")
    @classmethod
    def resolve_env_vars(cls, v: Optional[str]) -> Optional[str]:
        """Resolve ${ENV_VAR} references in string fields."""
        if v is None:
            return v

        # Pattern: ${VAR_NAME}
        pattern = r"\$\{([^}]+)\}"

        def replacer(match):
            env_var = match.group(1)
            value = os.getenv(env_var)
            if value is None:
                raise ValueError(
                    f"Environment variable '{env_var}' is not set. "
                    f"Required for configuration."
                )
            return value

        return re.sub(pattern, replacer, v)


# Discriminated union - Pydantic uses 'type' field to determine which model to use
AdapterConfig = Annotated[
    Union[CLIAdapterConfig, HTTPAdapterConfig], Field(discriminator="type")
]


class CLIToolConfig(BaseModel):
    """Configuration for a single CLI tool (legacy, deprecated)."""

    command: str
    args: list[str]
    timeout: int


class DefaultsConfig(BaseModel):
    """Default settings."""

    mode: str
    rounds: int
    max_rounds: int
    timeout_per_round: int


class StorageConfig(BaseModel):
    """Storage configuration."""

    transcripts_dir: str
    format: str
    auto_export: bool


class ConvergenceDetectionConfig(BaseModel):
    """Convergence detection configuration."""

    enabled: bool
    semantic_similarity_threshold: float
    divergence_threshold: float
    min_rounds_before_check: int
    consecutive_stable_rounds: int
    stance_stability_threshold: float
    response_length_drop_threshold: float


class EarlyStoppingConfig(BaseModel):
    """Model-controlled early stopping configuration."""

    enabled: bool
    threshold: float  # Fraction of models that must want to stop (e.g., 0.66 = 2/3)
    respect_min_rounds: bool  # Whether to respect defaults.rounds before stopping


class DeliberationConfig(BaseModel):
    """Deliberation engine configuration."""

    convergence_detection: ConvergenceDetectionConfig
    early_stopping: EarlyStoppingConfig
    convergence_threshold: float
    enable_convergence_detection: bool


class Config(BaseModel):
    """Root configuration model."""

    version: str

    # New adapters section (preferred)
    adapters: Optional[dict[str, AdapterConfig]] = None

    # Legacy cli_tools section (deprecated)
    cli_tools: Optional[dict[str, CLIToolConfig]] = None

    defaults: DefaultsConfig
    storage: StorageConfig
    deliberation: DeliberationConfig

    def model_post_init(self, __context):
        """Post-initialization validation."""
        if self.adapters is None and self.cli_tools is None:
            raise ValueError(
                "Configuration must include either 'adapters' or 'cli_tools' section"
            )

        # If cli_tools is used, emit deprecation warning
        if self.cli_tools is not None and self.adapters is None:
            warnings.warn(
                "The 'cli_tools' configuration section is deprecated. "
                "Please migrate to 'adapters' section with explicit 'type' field. "
                "See migration guide: docs/migration/cli_tools_to_adapters.md",
                DeprecationWarning,
                stacklevel=2,
            )


def load_config(path: str = "config.yaml") -> Config:
    """
    Load configuration from YAML file.

    Args:
        path: Path to config file (default: config.yaml)

    Returns:
        Validated Config object

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config is invalid
    """
    # Load environment variables from .env file (if it exists)
    load_dotenv()

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return Config(**data)
