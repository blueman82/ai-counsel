# Model Registry & MCP Model Picker

This guide explains how AI Counsel keeps track of valid model identifiers and how MCP clients can surface them through dropdowns or helper tools.

## 1. Configure the Registry in `config.yaml`

The `model_registry` section enumerates the allowlisted models for each adapter. Each entry contains:

- `id` – exact identifier passed to the adapter
- `label` – human friendly display text
- `tier` – optional hint (speed, premium, etc.)
- `default` – `true` marks the recommended fallback if a model isn't supplied
- `enabled` – `true` (default) makes model active and available; `false` hides it without deleting
- `note` – optional descriptive text shown in tool UIs

```yaml
model_registry:
  claude:
    - id: "claude-sonnet-4-5-20250929"
      label: "Claude Sonnet 4.5"
      tier: "balanced"
      default: true
      enabled: true  # Active model (default value, can be omitted)
    - id: "claude-haiku-4-5-20251001"
      label: "Claude Haiku 4.5"
      tier: "speed"
      enabled: true
    - id: "claude-opus-4-20250514"
      label: "Claude Opus 4"
      tier: "premium"
      enabled: false  # Disabled model - hidden but configuration retained
  codex:
    - id: "gpt-5-codex"
      label: "GPT-5 Codex"
      default: true
    - id: "gpt-5"
      label: "GPT-5"
      tier: "general"
      enabled: false  # Temporarily disabled for cost control
```

Adapters not listed here remain unrestricted (e.g., `ollama`, `llamacpp`).

## 2. Discover Models with `list_models`

Clients can query the registry using the `list_models` MCP tool.

```json
// Request
{"name": "list_models", "arguments": {}}

// Response (excerpt)
{
  "models": {
    "claude": [
      {"id": "claude-sonnet-4-5-20250929", "label": "Claude Sonnet 4.5", "tier": "balanced", "default": true},
      {"id": "claude-haiku-4-5-20251001", "label": "Claude Haiku 4.5", "tier": "speed"}
    ],
    "codex": [
      {"id": "gpt-5-codex", "label": "GPT-5 Codex", "default": true},
      {"id": "gpt-5", "label": "GPT-5", "tier": "general"}
    ]
  },
  "recommended_defaults": {
    "claude": "claude-sonnet-4-5-20250929",
    "codex": "gpt-5-codex"
  },
  "session_defaults": {}
}
```

Pass an `adapter` argument (e.g., `{ "adapter": "claude" }`) to retrieve a single list.

## 3. Override Session Defaults with `set_session_models`

`set_session_models` stores in-memory overrides for the active MCP session. Provide model IDs from the registry; use `null` to clear an override.

```json
// Request: prefer Haiku for Claude and Codex
{
  "name": "set_session_models",
  "arguments": {
    "claude": "claude-haiku-4-5-20251001",
    "codex": "gpt-5"
  }
}

// Response
{
  "status": "updated",
  "updates": {
    "claude": "claude-haiku-4-5-20251001",
    "codex": "gpt-5"
  },
  "session_defaults": {
    "claude": "claude-haiku-4-5-20251001",
    "codex": "gpt-5"
  }
}
```

These overrides live only for the running server process; restart the MCP server to reset them.

## 4. Running `deliberate`

- If a participant omits the `model` field, AI Counsel uses the session override (if any) or the registry default.
- Supplying a model not in the registry raises a validation error with the allowlisted options.
- MCP clients that honor JSON Schema `anyOf` will render dropdowns automatically thanks to the registry-backed schema emitted in `list_tools`.

## 5. The `enabled` Field: Toggling Models Without Deletion

The `enabled` field allows you to control model availability without losing configuration.

### Behavior

**When `enabled: true` (default):**
- Model appears in `list_models` responses
- Model can be selected in `deliberate` calls
- Model is considered for default selection
- Model included in `allowed_ids()` validation

**When `enabled: false`:**
- Model hidden from `list_models` responses
- Model rejected if specified in `deliberate` calls (validation error)
- Model skipped when selecting defaults
- Model excluded from `allowed_ids()` validation
- Model definition retained in config for easy re-enabling

### Examples

**Disabling an expensive model temporarily:**
```yaml
model_registry:
  claude:
    - id: "claude-opus-4-20250514"
      label: "Claude Opus 4"
      tier: "premium"
      enabled: false  # Disabled to control API costs
```

**Staging a new model before production:**
```yaml
model_registry:
  codex:
    - id: "gpt-5-codex-preview"
      label: "GPT-5 Codex Preview"
      tier: "experimental"
      enabled: false  # Configured but not yet active
```

**Disabling slow models during testing:**
```yaml
model_registry:
  gemini:
    - id: "gemini-2.5-pro"
      label: "Gemini 2.5 Pro"
      enabled: false  # Skip during rapid test iterations
```

### Filtering Implementation

The `ModelRegistry` class automatically filters disabled models:

```python
# ModelRegistry.list() - Returns only enabled models
catalog = model_registry.list()
# {"claude": [{"id": "claude-sonnet-...", ...}]}  # Only enabled models

# ModelRegistry.list_for_adapter() - Returns enabled RegistryEntry objects
entries = model_registry.list_for_adapter("claude")
# [RegistryEntry(id="...", enabled=True), ...]  # Only enabled entries

# ModelRegistry.allowed_ids() - Returns set of enabled model IDs
allowed = model_registry.allowed_ids("claude")
# {"claude-sonnet-4-5-20250929"}  # Only enabled IDs

# ModelRegistry.get_default() - Returns first enabled default
default = model_registry.get_default("claude")
# "claude-sonnet-4-5-20250929"  # Only if enabled

# ModelRegistry.is_allowed() - Checks if model exists AND is enabled
is_ok = model_registry.is_allowed("claude", "claude-opus-4-20250514")
# False (model exists but enabled=false)
```

### Use Cases

1. **Cost Control**: Disable expensive models during budget constraints
2. **Testing**: Enable only fast models during development, full set in production
3. **Staged Rollout**: Add model with `enabled: false`, test configuration, then enable
4. **Performance Tuning**: Disable slow models to reduce deliberation latency
5. **Compliance**: Temporarily restrict models pending security/legal approval
6. **Maintenance**: Disable models during provider outages without losing config
7. **A/B Testing**: Toggle between model configurations without editing IDs

### Best Practices

- Use `enabled: false` instead of deleting model definitions
- Add comments explaining why a model is disabled (e.g., "cost control", "staging")
- Document re-enabling criteria (e.g., "enable after budget reset")
- For permanent removal, delete the entire model definition
- Test default selection behavior after disabling the current default

## 6. Updating the Registry when Adding Adapters

When you introduce a new CLI/HTTP adapter, add its supported models to `model_registry` and document them. This keeps the picker UI accurate and prevents users from selecting unsupported IDs. See [Adding Adapters](adding-adapters.md) for the full workflow.
