# Model Registry & MCP Model Picker

This guide explains how AI Counsel keeps track of valid model identifiers and how MCP clients can surface them through dropdowns or helper tools.

## 1. Configure the Registry in `config.yaml`

The `model_registry` section enumerates the allowlisted models for each adapter. Each entry contains:

- `id` – exact identifier passed to the adapter
- `label` – human friendly display text
- `tier` – optional hint (speed, premium, etc.)
- `default` – `true` marks the recommended fallback if a model isn’t supplied
- `note` – optional descriptive text shown in tool UIs

```yaml
model_registry:
  claude:
    - id: "claude-sonnet-4-5-20250929"
      label: "Claude Sonnet 4.5"
      tier: "balanced"
      default: true
    - id: "claude-haiku-4-5-20251001"
      label: "Claude Haiku 4.5"
      tier: "speed"
  codex:
    - id: "gpt-5-codex"
      label: "GPT-5 Codex"
      default: true
    - id: "gpt-5"
      label: "GPT-5"
      tier: "general"
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

## 5. Updating the Registry when Adding Adapters

When you introduce a new CLI/HTTP adapter, add its supported models to `model_registry` and document them. This keeps the picker UI accurate and prevents users from selecting unsupported IDs. See [Adding Adapters](adding-adapters.md) for the full workflow.
