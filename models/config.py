"""Configuration loading and validation."""
from pathlib import Path
import yaml
from pydantic import BaseModel


class CLIToolConfig(BaseModel):
    """Configuration for a single CLI tool."""
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


class DeliberationConfig(BaseModel):
    """Deliberation engine configuration."""
    convergence_detection: ConvergenceDetectionConfig
    convergence_threshold: float
    enable_convergence_detection: bool


class Config(BaseModel):
    """Root configuration model."""
    version: str
    cli_tools: dict[str, CLIToolConfig]
    defaults: DefaultsConfig
    storage: StorageConfig
    deliberation: DeliberationConfig


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
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return Config(**data)
