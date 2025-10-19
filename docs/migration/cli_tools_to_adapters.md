# Migration Guide: cli_tools → adapters

## Why This Change?

The `cli_tools` configuration section has been renamed to `adapters` to better reflect the system's architecture. AI Counsel now supports both CLI-based adapters (claude, codex, etc.) and HTTP-based adapters (Ollama, LM Studio, OpenRouter).

The new `adapters` section uses an explicit `type` field to distinguish between adapter types, making the configuration more maintainable and future-proof.

## What Changed?

### Before (Deprecated)
```yaml
cli_tools:
  claude:
    command: "claude"
    args: ["--model", "{model}", "{prompt}"]
    timeout: 60
```

### After (Current)
```yaml
adapters:
  claude:
    type: cli  # ← Explicit type field
    command: "claude"
    args: ["--model", "{model}", "{prompt}"]
    timeout: 60
```

## Migration Options

### Option 1: Automatic Migration (Recommended)

Use the provided migration script:

```bash
python scripts/migrate_config.py config.yaml
```

This will:
1. Create a backup at `config.yaml.bak`
2. Convert `cli_tools` to `adapters` with `type: cli` added
3. Preserve all other configuration unchanged

**Output example:**
```
Migrating config: config.yaml
--------------------------------------------------
Created backup: config.yaml.bak
Success: Migrated 4 CLI tools to adapters format
Migrated config written to: config.yaml

Info: Review the changes and delete config.yaml.bak when satisfied.

Migration complete!

Next steps:
1. Review the migrated config.yaml
2. Test loading: python -c 'from models.config import load_config; load_config()'
3. Delete backup if satisfied: rm config.yaml.bak
```

### Option 2: Manual Migration

1. Rename `cli_tools:` to `adapters:`
2. Add `type: cli` to each adapter entry
3. Verify with: `python -c "from models.config import load_config; load_config()"`

## Backward Compatibility

**The `cli_tools` section still works** but will emit a deprecation warning:

```
DeprecationWarning: The 'cli_tools' configuration section is deprecated.
Please migrate to 'adapters' section with explicit 'type' field.
See migration guide: docs/migration/cli_tools_to_adapters.md
```

Support for `cli_tools` will be removed in **version 2.0**.

## New HTTP Adapter Format

The new structure also supports HTTP-based adapters:

```yaml
adapters:
  ollama:
    type: http  # ← HTTP adapter type
    base_url: "http://localhost:11434"
    timeout: 60

  openrouter:
    type: http
    base_url: "https://openrouter.ai/api/v1"
    api_key: "${OPENROUTER_API_KEY}"  # ← Environment variable
    timeout: 90
    max_retries: 3
```

### Environment Variables

HTTP adapters support environment variable substitution for secure API key storage:

```yaml
adapters:
  openrouter:
    type: http
    base_url: "https://openrouter.ai/api/v1"
    api_key: "${OPENROUTER_API_KEY}"  # Will be replaced with actual value
```

Set the environment variable:
```bash
export OPENROUTER_API_KEY="your-key-here"
```

Or add to `.env` file if using python-dotenv.

## Complete Example

### Before Migration
```yaml
version: "1.0"

cli_tools:
  claude:
    command: "claude"
    args: ["-p", "--model", "{model}", "--settings", '{"disableAllHooks": true}', "{prompt}"]
    timeout: 300

  codex:
    command: "codex"
    args: ["exec", "--model", "{model}", "{prompt}"]
    timeout: 180

defaults:
  mode: "quick"
  rounds: 2
  max_rounds: 5
  timeout_per_round: 120

# ... rest of config
```

### After Migration
```yaml
version: "1.0"

adapters:
  # CLI adapters (migrated from cli_tools)
  claude:
    type: cli
    command: "claude"
    args: ["-p", "--model", "{model}", "--settings", '{"disableAllHooks": true}', "{prompt}"]
    timeout: 300

  codex:
    type: cli
    command: "codex"
    args: ["exec", "--model", "{model}", "{prompt}"]
    timeout: 180

  # HTTP adapters (new functionality)
  ollama:
    type: http
    base_url: "http://localhost:11434"
    timeout: 120
    max_retries: 3

defaults:
  mode: "quick"
  rounds: 2
  max_rounds: 5
  timeout_per_round: 120

# ... rest of config
```

## Troubleshooting

### Error: "Configuration must include either 'adapters' or 'cli_tools' section"

Your config is missing the adapter section. Add either `adapters:` or `cli_tools:` (deprecated).

### Error: "Environment variable 'XXX' is not set"

An HTTP adapter references an undefined environment variable. Set it:

```bash
export OPENROUTER_API_KEY="your-key-here"
```

Or add to `.env` file if using python-dotenv.

### Warning: DeprecationWarning about cli_tools

This is expected if you're still using the `cli_tools` section. Run the migration script to update to the new format:

```bash
python scripts/migrate_config.py config.yaml
```

### Migration script fails with "Config file not found"

Ensure you're providing the correct path to your config file:

```bash
python scripts/migrate_config.py /path/to/your/config.yaml
```

Or run from the project root directory if using the default `config.yaml`.

## Benefits of the New Format

1. **Type Safety**: Explicit `type` field makes configuration intent clear
2. **Extensibility**: Easy to add new adapter types (HTTP, gRPC, etc.)
3. **Better Validation**: Pydantic validates each adapter type separately
4. **Future-Proof**: Prepared for additional adapter types beyond CLI and HTTP

## Questions?

- See the main [README](../../README.md) for general documentation
- See [CLAUDE.md](../../CLAUDE.md) for development documentation
- Open an issue on GitHub for migration-related problems
