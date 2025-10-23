"""Configuration loading and validation."""
import os
import re
import warnings
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


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
    def resolve_env_vars(cls, v: Optional[str], info) -> Optional[str]:
        """Resolve ${ENV_VAR} references in string fields.

        For optional fields like api_key:
        - If env var is missing, returns None (allows graceful degradation)

        For required fields like base_url:
        - If env var is missing, raises ValueError
        """
        if v is None:
            return v

        # Pattern: ${VAR_NAME}
        pattern = r"\$\{([^}]+)\}"

        def replacer(match):
            env_var = match.group(1)
            value = os.getenv(env_var)
            if value is None:
                # For optional fields, return None if env var is missing
                if info.field_name == "api_key":
                    return None  # type: ignore
                # For required fields, raise error
                raise ValueError(
                    f"Environment variable '{env_var}' is not set. "
                    f"Required for configuration."
                )
            return value

        result = re.sub(pattern, replacer, v)
        # If result contains None sentinel values (from api_key missing), return None
        if info.field_name == "api_key" and result == "None":
            return None
        return result


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


class DecisionGraphConfig(BaseModel):
    """Configuration for decision graph memory."""

    enabled: bool = Field(False, description="Enable decision graph memory")
    db_path: str = Field("decision_graph.db", description="Path to SQLite database")

    # DEPRECATED: Use tier_boundaries instead. Kept for backward compatibility.
    similarity_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="DEPRECATED: Minimum similarity score for context injection. Use tier_boundaries instead.",
    )

    max_context_decisions: int = Field(
        3,
        ge=1,
        le=10,
        description="Maximum number of past decisions to inject as context",
    )
    compute_similarities: bool = Field(
        True, description="Compute similarities after storing a deliberation"
    )

    # NEW: Budget-aware context injection parameters
    context_token_budget: int = Field(
        1500,
        ge=500,
        le=10000,
        description="Maximum tokens allowed for context injection (prevents token bloat)"
    )

    tier_boundaries: dict[str, float] = Field(
        default_factory=lambda: {"strong": 0.75, "moderate": 0.60},
        description="Similarity score boundaries for tiered injection (strong > moderate > 0)"
    )

    query_window: int = Field(
        1000,
        ge=50,
        le=10000,
        description="Number of recent decisions to query for scalability"
    )

    @field_validator("tier_boundaries")
    @classmethod
    def validate_tier_boundaries(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate tier boundaries: strong > moderate > 0."""
        if not isinstance(v, dict) or "strong" not in v or "moderate" not in v:
            raise ValueError("tier_boundaries must have 'strong' and 'moderate' keys")

        if not (0.0 < v["moderate"] < v["strong"] <= 1.0):
            raise ValueError(
                f"tier_boundaries must satisfy: 0 < moderate ({v['moderate']}) "
                f"< strong ({v['strong']}) <= 1"
            )

        return v

    @field_validator("db_path")
    @classmethod
    def resolve_db_path(cls, v: str) -> str:
        """
        Resolve db_path to absolute path relative to project root.

        This validator ensures that relative database paths are always resolved
        relative to the project root directory (where config.yaml is located),
        not the current working directory. This prevents breakage when running
        the server from different directories.

        Processing steps:
        1. Resolve ${ENV_VAR} environment variable references
        2. Convert relative paths to absolute paths relative to project root
        3. Keep absolute paths unchanged
        4. Return normalized absolute path as string

        Examples:
            "decision_graph.db" → "/path/to/project/decision_graph.db"
            "/tmp/foo.db" → "/tmp/foo.db" (unchanged)
            "${DATA_DIR}/graph.db" → "/var/data/graph.db" (if DATA_DIR=/var/data)
            "../shared/graph.db" → "/path/to/shared/graph.db"

        Args:
            v: Database path from configuration (may contain env vars)

        Returns:
            Absolute path as string

        Raises:
            ValueError: If environment variable is referenced but not set
        """
        # Step 1: Resolve environment variables using ${VAR_NAME} pattern
        pattern = r"\$\{([^}]+)\}"

        def replacer(match):
            env_var = match.group(1)
            value = os.getenv(env_var)
            if value is None:
                raise ValueError(
                    f"Environment variable '{env_var}' is not set. "
                    f"Required for db_path configuration."
                )
            return value

        resolved = re.sub(pattern, replacer, v)

        # Step 2: Convert to Path object
        path = Path(resolved)

        # Step 3: If relative, make it relative to project root
        if not path.is_absolute():
            # This file is at: project_root/models/config.py
            # Project root is two levels up from this file
            project_root = Path(__file__).parent.parent
            path = (project_root / path).resolve()

        # Step 4: Return as string (normalized, absolute)
        return str(path)


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
    decision_graph: Optional[DecisionGraphConfig] = None

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
