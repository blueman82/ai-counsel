"""Tests for the model registry utility."""
import pytest

from models.config import Config, load_config
from models.model_registry import ModelRegistry


@pytest.fixture(scope="module")
def registry() -> ModelRegistry:
    config = load_config()
    return ModelRegistry(config)


def test_registry_lists_models(registry: ModelRegistry):
    claude_entries = registry.list_for_adapter("claude")
    assert claude_entries, "Expected allowlisted Claude models"
    assert claude_entries[0].id == "claude-sonnet-4-5-20250929"
    assert registry.get_default("claude") == "claude-sonnet-4-5-20250929"


def test_registry_enforces_allowlist(registry: ModelRegistry):
    assert registry.is_allowed("claude", "claude-haiku-4-5-20251001") is True
    assert registry.is_allowed("claude", "non-existent-model") is False


def test_registry_is_permissive_for_unmanaged_adapters(registry: ModelRegistry):
    # Adapters with no registry (e.g., llamacpp) accept any model name
    assert registry.is_allowed("llamacpp", "/path/to/model.gguf") is True


# ============================================================================
# Tests for enabled field feature
# ============================================================================


def _minimal_config(model_registry: dict) -> Config:
    """Helper to create minimal Config for testing model registry."""
    return Config.model_validate(
        {
            "version": "1.0",
            "cli_tools": {"test": {"command": "test", "args": [], "timeout": 60}},
            "defaults": {
                "mode": "quick",
                "rounds": 2,
                "max_rounds": 5,
                "timeout_per_round": 120,
            },
            "storage": {
                "transcripts_dir": "transcripts",
                "format": "markdown",
                "auto_export": True,
            },
            "deliberation": {
                "convergence_detection": {
                    "enabled": True,
                    "semantic_similarity_threshold": 0.85,
                    "divergence_threshold": 0.40,
                    "min_rounds_before_check": 1,
                    "consecutive_stable_rounds": 2,
                    "stance_stability_threshold": 0.80,
                    "response_length_drop_threshold": 0.50,
                },
                "early_stopping": {
                    "enabled": True,
                    "threshold": 0.66,
                    "respect_min_rounds": True,
                },
                "convergence_threshold": 0.85,
                "enable_convergence_detection": True,
            },
            "model_registry": model_registry,
        }
    )


@pytest.fixture
def config_with_enabled_models() -> Config:
    """Create a config with mix of enabled and disabled models."""
    return _minimal_config(
        {
            "test_adapter": [
                {
                    "id": "model-enabled-1",
                    "label": "Enabled Model 1",
                    "enabled": True,
                    "default": True,
                },
                {"id": "model-enabled-2", "label": "Enabled Model 2", "enabled": True},
                {
                    "id": "model-disabled-1",
                    "label": "Disabled Model 1",
                    "enabled": False,
                },
                {
                    "id": "model-disabled-2",
                    "label": "Disabled Model 2",
                    "enabled": False,
                },
            ]
        }
    )


@pytest.fixture
def config_with_implicit_enabled() -> Config:
    """Create a config with models that don't specify enabled field."""
    return _minimal_config(
        {
            "test_adapter": [
                {"id": "model-implicit-1", "label": "Implicitly Enabled Model 1"},
                {
                    "id": "model-implicit-2",
                    "label": "Implicitly Enabled Model 2",
                    "default": True,
                },
            ]
        }
    )


@pytest.fixture
def config_with_all_disabled() -> Config:
    """Create a config where all models are disabled."""
    return _minimal_config(
        {
            "test_adapter": [
                {
                    "id": "model-disabled-1",
                    "label": "Disabled Model 1",
                    "enabled": False,
                },
                {
                    "id": "model-disabled-2",
                    "label": "Disabled Model 2",
                    "enabled": False,
                },
            ]
        }
    )


@pytest.fixture
def config_with_empty_registry() -> Config:
    """Create a config with empty model registry."""
    return _minimal_config({"test_adapter": []})


def test_list_for_adapter_returns_only_enabled_models(
    config_with_enabled_models: Config,
):
    """Test that list_for_adapter() filters out disabled models."""
    registry = ModelRegistry(config_with_enabled_models)

    enabled_models = registry.list_for_adapter("test_adapter")

    # Should only return enabled models
    assert len(enabled_models) == 2
    assert all(entry.id.startswith("model-enabled") for entry in enabled_models)

    # Verify specific models are present
    model_ids = {entry.id for entry in enabled_models}
    assert "model-enabled-1" in model_ids
    assert "model-enabled-2" in model_ids

    # Verify disabled models are not present
    assert "model-disabled-1" not in model_ids
    assert "model-disabled-2" not in model_ids


def test_list_for_adapter_with_disabled_models_excludes_them(
    config_with_enabled_models: Config,
):
    """Test that disabled models are explicitly excluded from results."""
    registry = ModelRegistry(config_with_enabled_models)

    enabled_models = registry.list_for_adapter("test_adapter")

    # None of the returned entries should have disabled models
    for entry in enabled_models:
        assert "disabled" not in entry.id.lower()


def test_backward_compatibility_models_without_enabled_field_default_to_true(
    config_with_implicit_enabled: Config,
):
    """Test that models without explicit enabled field default to enabled=True."""
    registry = ModelRegistry(config_with_implicit_enabled)

    models = registry.list_for_adapter("test_adapter")

    # All models should be returned (default enabled=True)
    assert len(models) == 2
    assert models[0].id == "model-implicit-2"  # default=True comes first
    assert models[1].id == "model-implicit-1"


def test_get_all_models_returns_all_regardless_of_enabled_status(
    config_with_enabled_models: Config,
):
    """Test that get_all_models() returns both enabled and disabled models."""
    registry = ModelRegistry(config_with_enabled_models)

    all_models = registry.get_all_models("test_adapter")

    # Should return all 4 models (2 enabled + 2 disabled)
    assert len(all_models) == 4

    model_ids = {entry.id for entry in all_models}
    assert "model-enabled-1" in model_ids
    assert "model-enabled-2" in model_ids
    assert "model-disabled-1" in model_ids
    assert "model-disabled-2" in model_ids


def test_get_all_models_preserves_ordering(config_with_enabled_models: Config):
    """Test that get_all_models() preserves the registry ordering."""
    registry = ModelRegistry(config_with_enabled_models)

    all_models = registry.get_all_models("test_adapter")

    # Default model should come first
    assert all_models[0].id == "model-enabled-1"
    assert all_models[0].default is True


def test_empty_registry_returns_empty_list(config_with_empty_registry: Config):
    """Test behavior with empty model registry."""
    registry = ModelRegistry(config_with_empty_registry)

    enabled_models = registry.list_for_adapter("test_adapter")
    all_models = registry.get_all_models("test_adapter")

    assert len(enabled_models) == 0
    assert len(all_models) == 0


def test_all_disabled_models_returns_empty_enabled_list(
    config_with_all_disabled: Config,
):
    """Test that when all models are disabled, list_for_adapter returns empty."""
    registry = ModelRegistry(config_with_all_disabled)

    enabled_models = registry.list_for_adapter("test_adapter")

    # No enabled models
    assert len(enabled_models) == 0


def test_all_disabled_models_but_get_all_returns_all(config_with_all_disabled: Config):
    """Test that get_all_models() still returns disabled models."""
    registry = ModelRegistry(config_with_all_disabled)

    all_models = registry.get_all_models("test_adapter")

    # Should return all disabled models
    assert len(all_models) == 2
    model_ids = {entry.id for entry in all_models}
    assert "model-disabled-1" in model_ids
    assert "model-disabled-2" in model_ids


def test_nonexistent_adapter_returns_empty_lists():
    """Test behavior when querying adapter that doesn't exist."""
    config = _minimal_config({})
    registry = ModelRegistry(config)

    enabled_models = registry.list_for_adapter("nonexistent")
    all_models = registry.get_all_models("nonexistent")

    assert len(enabled_models) == 0
    assert len(all_models) == 0


def test_allowed_ids_only_includes_enabled_models(config_with_enabled_models: Config):
    """Test that allowed_ids() only includes enabled models."""
    registry = ModelRegistry(config_with_enabled_models)

    allowed = registry.allowed_ids("test_adapter")

    # Should only include enabled models
    assert len(allowed) == 2
    assert "model-enabled-1" in allowed
    assert "model-enabled-2" in allowed
    assert "model-disabled-1" not in allowed
    assert "model-disabled-2" not in allowed


def test_is_allowed_returns_false_for_disabled_models(
    config_with_enabled_models: Config,
):
    """Test that is_allowed() returns False for disabled models."""
    registry = ModelRegistry(config_with_enabled_models)

    # Enabled models should be allowed
    assert registry.is_allowed("test_adapter", "model-enabled-1") is True
    assert registry.is_allowed("test_adapter", "model-enabled-2") is True

    # Disabled models should NOT be allowed
    assert registry.is_allowed("test_adapter", "model-disabled-1") is False
    assert registry.is_allowed("test_adapter", "model-disabled-2") is False


def test_get_default_ignores_disabled_models():
    """Test that get_default() skips disabled models even if marked as default."""
    config = _minimal_config(
        {
            "test_adapter": [
                {
                    "id": "model-disabled-default",
                    "label": "Disabled Default",
                    "enabled": False,
                    "default": True,
                },
                {
                    "id": "model-enabled-fallback",
                    "label": "Enabled Fallback",
                    "enabled": True,
                },
            ]
        }
    )
    registry = ModelRegistry(config)

    # Should skip disabled default and return first enabled model
    default = registry.get_default("test_adapter")
    assert default == "model-enabled-fallback"


def test_get_default_with_all_disabled_returns_none(config_with_all_disabled: Config):
    """Test that get_default() returns None when all models are disabled."""
    registry = ModelRegistry(config_with_all_disabled)

    default = registry.get_default("test_adapter")
    assert default is None


def test_mixed_enabled_disabled_maintains_ordering():
    """Test that enabled filtering preserves original order."""
    config = _minimal_config(
        {
            "test_adapter": [
                {
                    "id": "model-z-enabled",
                    "label": "Z Enabled",
                    "enabled": True,
                    "default": True,
                },
                {"id": "model-a-disabled", "label": "A Disabled", "enabled": False},
                {"id": "model-m-enabled", "label": "M Enabled", "enabled": True},
            ]
        }
    )
    registry = ModelRegistry(config)

    enabled_models = registry.list_for_adapter("test_adapter")

    # Should have 2 enabled models in original order (default first, then alphabetical)
    assert len(enabled_models) == 2
    assert enabled_models[0].id == "model-z-enabled"  # default=True comes first
    assert enabled_models[1].id == "model-m-enabled"


def test_enabled_field_is_stored_in_registry_entry():
    """Test that enabled status is preserved in RegistryEntry."""
    config = _minimal_config(
        {"test_adapter": [{"id": "model-1", "label": "Model 1", "enabled": True}]}
    )
    registry = ModelRegistry(config)

    # This tests that the enabled field is properly handled during construction
    # Even though RegistryEntry doesn't expose enabled, the filtering works
    models = registry.list_for_adapter("test_adapter")
    assert len(models) == 1
    assert models[0].id == "model-1"
