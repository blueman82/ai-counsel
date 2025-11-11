# Model Enable/Disable Feature - Issues Summary

## 🔴 CRITICAL (1)

### Config Syntax Error
- **File**: `config.yaml`, line 175
- **Current**: `enabled: disable`
- **Should be**: `enabled: false`
- **Impact**: Breaks 6 tests in `test_config.py`
- **Fix**: Change `disable` to `false`
- **Time to Fix**: < 1 minute

```yaml
# WRONG (current):
- id: "claude-opus-4-1-20250805"
  enabled: disable

# RIGHT (should be):
- id: "claude-opus-4-1-20250805"
  enabled: false
```

---

## 🟠 MEDIUM (1)

### Ambiguous Default Selection with Disabled Defaults
- **File**: `models/model_registry.py`, lines 79-92 (`get_default()`)
- **Issue**: When marked default model is disabled, silently skips to first enabled
- **Current**: Behavior is correct, but lacks audit trail
- **Recommendation**: Add debug log when fallback occurs
- **Time to Fix**: 5 minutes
- **Code Location**: `get_default()` method after trying marked defaults

```python
# Add this after trying to find marked default:
if all_marked_defaults and all_marked_defaults[0].id != first_enabled.id:
    logger.debug(
        f"Marked default '{all_marked_defaults[0].id}' is disabled for '{cli}'. "
        f"Using fallback: '{first_enabled.id}'"
    )
```

---

## 🟡 MINOR (2)

### Missing RegistryEntry Docstring
- **File**: `models/model_registry.py`, lines 9-15
- **Issue**: RegistryEntry has `enabled` field but no field-level documentation
- **Recommendation**: Add docstring with field descriptions
- **Time to Fix**: 2 minutes

```python
@dataclass(frozen=True)
class RegistryEntry:
    """Normalized model definition entry.
    
    Attributes:
        id: Unique model identifier
        label: Human-friendly display name
        tier: Optional tier classification
        note: Optional guidance text
        default: Whether marked as default
        enabled: Whether model is active and available
    """
```

### No Audit Logging for Disabled Model Requests
- **File**: `server.py`, function `call_tool()` (around line 400)
- **Issue**: When user requests disabled model, error is clear but no log entry
- **Recommendation**: Log when disabled vs. non-existent models are requested
- **Time to Fix**: 5 minutes
- **Benefit**: Better operational visibility for debugging

```python
# Add in server.py after is_allowed() check:
all_models = model_registry.get_all_models(cli)
all_ids = {e.id for e in all_models}

if provided_model in all_ids:
    logger.warning(
        f"User requested disabled model '{provided_model}' for adapter '{cli}'"
    )
```

---

## 📋 What's Working Well (No Issues)

✅ **Type Safety**: Pydantic schema is correct with proper defaults  
✅ **Filtering Logic**: All registry methods correctly filter disabled models  
✅ **Tests**: 18/18 tests pass (once config is fixed, 46/46 config tests will pass)  
✅ **Documentation**: CLAUDE.md, README, and docs/ are complete  
✅ **Backward Compatibility**: Omitting `enabled` field defaults to `true`  
✅ **MCP Integration**: Server validates disabled models correctly  
✅ **Security**: No vulnerabilities found  
✅ **Performance**: O(n) filtering on small sets is acceptable  

---

## Summary

| Severity | Count | Time to Fix |
|----------|-------|------------|
| 🔴 Critical | 1 | 1 min |
| 🟠 Medium | 1 | 5 min |
| 🟡 Minor | 2 | 7 min |
| **Total** | **4** | **~13 min** |

**All issues are non-blocking for the most part, except the CRITICAL config syntax error which must be fixed before tests can pass.**
