"""Model registry utilities derived from configuration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, Optional
import builtins

from models.config import Config, ModelDefinition

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegistryEntry:
    """Normalized model definition entry.
    
    Attributes:
        id: Unique model identifier used by adapter
        label: Human-friendly display name for UI dropdowns
        tier: Optional tier classification (speed, premium, coding, etc.)
        note: Optional descriptive text shown in model picker tooltips
        default: Whether marked as recommended default for this adapter
        enabled: Whether model is active and available for use
    """

    id: str
    label: str
    tier: Optional[str] = None
    note: Optional[str] = None
    default: bool = False
    enabled: bool = True


class ModelRegistry:
    """In-memory view of configured model options per adapter."""

    def __init__(self, config: Config):
        self._entries: Dict[str, list[RegistryEntry]] = {}

        registry_cfg = getattr(config, "model_registry", None) or {}
        for cli, models in registry_cfg.items():
            normalized = []
            for model in models:
                # Pydantic ensures the structure, but guard against None just in case
                if isinstance(model, ModelDefinition):
                    model_def = model
                else:
                    model_def = ModelDefinition.model_validate(model)

                normalized.append(
                    RegistryEntry(
                        id=model_def.id,
                        label=model_def.label or model_def.id,
                        tier=model_def.tier,
                        note=model_def.note,
                        default=bool(model_def.default),
                        enabled=bool(model_def.enabled),
                    )
                )

            # Ensure deterministic ordering (defaults first, then alphabetical)
            normalized.sort(
                key=lambda entry: (
                    not entry.default,
                    entry.label.lower(),
                )
            )
            self._entries[cli] = normalized

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def adapters(self) -> Iterable[str]:
        """Return adapter names with registry entries."""

        return self._entries.keys()

    def list(self) -> Dict[str, list[dict[str, str | bool]]]:
        """Return a serializable map of enabled model options by adapter."""

        result: Dict[str, list[dict[str, str | bool]]] = {}
        for cli, entries in self._entries.items():
            enabled_entries = [e for e in entries if e.enabled]
            result[cli] = [self._entry_to_dict(entry) for entry in enabled_entries]
        return result

    def list_for_adapter(self, cli: str) -> builtins.list[RegistryEntry]:
        """Return enabled entries for the given adapter (empty if none configured)."""

        entries = self._entries.get(cli, [])
        return [entry for entry in entries if entry.enabled]

    def get_all_models(self, cli: str) -> builtins.list[RegistryEntry]:
        """Return all entries for the given adapter, including disabled ones.

        Useful for administrative interfaces and debugging.
        """

        return builtins.list(self._entries.get(cli, []))

    def allowed_ids(self, cli: str) -> set[str]:
        """Return the set of allowed (enabled) model IDs for an adapter."""

        return {entry.id for entry in self._entries.get(cli, []) if entry.enabled}

    def get_default(self, cli: str) -> Optional[str]:
        """Return the default model id for an adapter, if configured.

        Only considers enabled models. If the marked default is disabled,
        returns the first enabled model. If no enabled models, returns None.
        """

        entries = self._entries.get(cli, [])
        if not entries:
            return None

        # Filter to enabled models only
        enabled_entries = [e for e in entries if e.enabled]
        if not enabled_entries:
            return None

        # Try to find the marked default among enabled models
        for entry in enabled_entries:
            if entry.default:
                return entry.id

        # Fallback to first enabled model
        # Check if we're skipping a disabled default (for operational visibility)
        all_defaults = [e for e in entries if e.default]
        if all_defaults and not all_defaults[0].enabled:
            logger.debug(
                f"Marked default '{all_defaults[0].id}' for adapter '{cli}' is disabled. "
                f"Falling back to first enabled model: '{enabled_entries[0].id}'"
            )
        
        return enabled_entries[0].id

    def is_allowed(self, cli: str, model_id: str) -> bool:
        """Check whether the given model id is allowlisted for the adapter."""

        if cli not in self._entries:
            return True  # Unrestricted adapter (e.g., open router, custom paths)
        return model_id in self.allowed_ids(cli)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _entry_to_dict(
        entry: RegistryEntry, include_enabled: bool = False
    ) -> dict[str, str | bool]:
        """Serialize an entry for MCP responses.

        Args:
            entry: Registry entry to serialize
            include_enabled: Whether to include the enabled status (useful for admin interfaces)
        """

        payload: dict[str, str | bool] = {
            "id": entry.id,
            "label": entry.label,
        }
        if entry.tier:
            payload["tier"] = entry.tier
        if entry.note:
            payload["note"] = entry.note
        if entry.default:
            payload["default"] = True
        if include_enabled:
            payload["enabled"] = entry.enabled
        return payload
