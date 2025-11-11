# Droid CLI Permission Level Research

## Executive Summary

**Key Finding**: The user's `~/.factory/settings.json` has `"autonomyMode": "spec"` which likely **locks droid in spec (read-only) mode**, preventing command execution even when `--auto` flags are provided via CLI.

**Answer to Core Question**: Based on the available evidence, **CLI flags may NOT override the `autonomyMode` config setting**. The droid adapter's current retry strategy (--auto low → medium → high) will fail if the config file forces spec mode.

## Critical Discovery: User's Config File

**Location**: `~/.factory/settings.json`

**Critical Settings**:
```json
{
  "autonomyMode": "spec",           // ← BLOCKS EXECUTION
  "autonomyLevel": "auto-high",     // ← CONFLICTS WITH ABOVE
  "commandAllowlist": ["ls", "pwd", "dir"],
  "commandDenylist": [...]
}
```

**Analysis**: The user has **conflicting settings**:
- `autonomyMode: "spec"` = Read-only mode (no execution)
- `autonomyLevel: "auto-high"` = Full autonomy (production operations)

This conflict suggests either:
1. Settings file schema changed between droid versions
2. `autonomyMode` overrides `autonomyLevel` 
3. Different parts of droid read different fields

## Configuration Hierarchy Research

### 1. Configuration File Locations

**Confirmed Paths**:
- **Settings**: `~/.factory/settings.json` (all platforms)
- **Custom Models**: `~/.factory/config.json` (for model definitions)
- **User Directives**: `~/.config/AGENTS.md` (global instructions)
- **Project Directives**: `./AGENTS.md` (project-specific, takes precedence)

**Precedence**: Based on GitHub issue #112, the hierarchy is:
1. Project-level config (`./AGENTS.md`)
2. User-level config (`~/.config/AGENTS.md`, `~/.factory/settings.json`)

### 2. Settings That Control Permissions

From `~/.factory/settings.json` schema:

**`autonomyMode`**: String field with values like `"spec"`, `"normal"`, `"auto-low"`, etc.
- Controls "how proactively droid executes commands when sessions begin"
- `"spec"` mode = read-only (planning/analysis only)

**`autonomyLevel`**: String field with values `"normal"`, `"auto-low"`, `"auto-medium"`, `"auto-high"`
- Controls default autonomy for sessions
- Appears to be newer field (may have replaced `autonomyMode`)

**`commandAllowlist`**: Array of strings
- Commands that run without confirmation
- User's list: `["ls", "pwd", "dir"]` (minimal)

**`commandDenylist`**: Array of strings  
- Commands that always require confirmation
- User has extensive dangerous command list

### 3. CLI Flags vs Config Settings

**From `droid exec --help`**:

```
--auto <level>              Autonomy level: low|medium|high
--skip-permissions-unsafe   Skip ALL permission checks - allows all permissions (unsafe)
```

**Critical Gap**: The help text does NOT mention:
- Whether `--auto` overrides config file settings
- Whether `--skip-permissions-unsafe` overrides `autonomyMode: "spec"`
- Any flag to force execution mode when config restricts it

**Error Message Analysis**:
```
insufficient permission to proceed. Re-run with --auto low|medium|high (to enable execution)
```

**Why This Is Suspicious**:
- Adapter already passes `--auto low` (then retries with medium/high)
- Droid suggests using `--auto` flags that are already present
- This indicates **config is overriding CLI flags**

### 4. Headless Mode Behavior

**From Documentation**:
- `droid exec` is "non-interactive single run that writes to stdout/stderr"
- Designed for "CI/CD integration"
- No special headless-specific flags mentioned

**Key Insight**: `droid exec` appears to respect the same config files as interactive mode. No evidence of different permission handling.

### 5. Override Mechanisms

**Available Nuclear Options**:

**`--skip-permissions-unsafe`**:
- "Bypass all checks - DANGEROUS!"
- "Allows ALL operations without confirmation"
- "Cannot be combined with --auto flags"
- **Unknown**: Whether this overrides `autonomyMode: "spec"` in config

**No Evidence Of**:
- `--force` flag
- `--ignore-config` flag
- `--override-autonomy` flag
- Environment variables like `DROID_AUTONOMY_OVERRIDE`

## Root Cause Analysis

### The Problem

The droid adapter implements graceful degradation:
```python
PERMISSION_LEVELS = ["low", "medium", "high"]
# Retries: --auto low → --auto medium → --auto high
```

But if `~/.factory/settings.json` has `"autonomyMode": "spec"`, this may **lock droid in read-only mode** regardless of `--auto` flags.

### Evidence Supporting Config Override

1. **User has spec mode set**: `"autonomyMode": "spec"` in settings
2. **Error message is misleading**: Suggests using flags that are already present
3. **All permission levels fail**: Even `--auto high` doesn't work
4. **No override flags documented**: No way to bypass config from CLI

### Evidence Against Config Override

1. **Conflicting settings exist**: User also has `"autonomyLevel": "auto-high"`
2. **Settings file shows confusion**: Two permission fields suggest schema evolution
3. **Documentation doesn't mention conflicts**: No guidance on precedence

## Recommended Solutions

### Option 1: Fix User's Config File (RECOMMENDED)

**Action**: Change `autonomyMode` to match `autonomyLevel`:

```json
{
  "autonomyMode": "auto-high",     // ← CHANGED FROM "spec"
  "autonomyLevel": "auto-high",
}
```

**Rationale**: 
- Aligns conflicting settings
- May allow `--auto` flags to work
- No code changes needed

### Option 2: Test `--skip-permissions-unsafe` Flag

**Action**: Modify adapter to use nuclear option:

```python
# In config.yaml
droid:
  command: "droid"
  args: ["exec", "--skip-permissions-unsafe", "-m", "{model}", "{prompt}"]
```

**Risks**:
- **DANGEROUS**: Bypasses all safety checks
- May still be overridden by `autonomyMode: "spec"`
- Cannot combine with `--auto` flags (lose graceful degradation)

### Option 3: Add Config Override Detection (FUTURE WORK)

**Action**: Adapter checks `~/.factory/settings.json` before running:

```python
def _check_autonomy_config(self):
    """Warn if user's config will block execution."""
    settings_path = Path.home() / ".factory" / "settings.json"
    if settings_path.exists():
        settings = json.loads(settings_path.read_text())
        if settings.get("autonomyMode") == "spec":
            logger.warning(
                "User's ~/.factory/settings.json has autonomyMode='spec'. "
                "This may block command execution. Consider changing to 'auto-high'."
            )
```

## Open Questions

1. **Does `autonomyMode: "spec"` override `--auto` flags?**
   - Documentation doesn't say
   - Need to test empirically

2. **What's the difference between `autonomyMode` and `autonomyLevel`?**
   - User has both fields with conflicting values
   - May indicate schema migration

3. **Does `--skip-permissions-unsafe` override spec mode?**
   - Not documented
   - Likely doesn't (would defeat purpose of config lock)

4. **Are there team/workspace policies we're missing?**
   - No evidence of Factory Dashboard enforcing policies
   - GitHub issues mention individual config files only

## Testing Plan

To definitively answer whether config overrides CLI:

```bash
# 1. Save current config
cp ~/.factory/settings.json ~/.factory/settings.json.backup

# 2. Test with spec mode
echo '{"autonomyMode": "spec"}' > ~/.factory/settings.json
droid exec --auto high "create file test.txt"
# Expected: Permission error

# 3. Test with auto-high mode  
echo '{"autonomyMode": "auto-high"}' > ~/.factory/settings.json
droid exec --auto high "create file test.txt"
# Expected: Success

# 4. Test skip-permissions-unsafe with spec mode
echo '{"autonomyMode": "spec"}' > ~/.factory/settings.json
droid exec --skip-permissions-unsafe "create file test.txt"
# Expected: ??? (this answers the key question)

# 5. Restore config
mv ~/.factory/settings.json.backup ~/.factory/settings.json
```

## Conclusion

**Immediate Action**: User should change `~/.factory/settings.json`:
```json
{
  "autonomyMode": "auto-high",  // ← FIX THIS
  "autonomyLevel": "auto-high"
}
```

**Why This Will Likely Work**:
- Resolves conflicting settings
- Aligns with user's apparent intent (they set `autonomyLevel: auto-high`)
- No code changes needed
- Maintains adapter's graceful degradation strategy

**If This Doesn't Work**: The nuclear option is `--skip-permissions-unsafe`, but this bypasses all safety checks and may still be blocked by spec mode.
