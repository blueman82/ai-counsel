# CLI Model Reference

Quick reference for model parameters accepted by each CLI tool.

## ✅ claude
- **Model parameter**: `--model <model>`
- **Valid values**: Aliases like `sonnet`, `opus`, `haiku` or full names like `claude-sonnet-4-5-20250929`
- **Tested working**: `sonnet` ✓
- **Test command**: `claude -p --model sonnet --settings '{"disableAllHooks": true}' "test"`

## ✅ droid
- **Model parameter**: `-m, --model <id>`
- **Default**: `gpt-5-codex`
- **Valid values**: `claude-opus-4-1-20250805`, `claude-sonnet-4-20250514`, `gpt-5-2025-08-07`, `gpt-5-codex`, `claude-sonnet-4-5-20250929`
- **Tested working**: `claude-sonnet-4-5-20250929` ✓
- **Test command**: `droid exec -m claude-sonnet-4-5-20250929 "test"`
- **Note**: Does NOT accept short aliases like `sonnet4.5` - use full model IDs

## ✅ gemini
- **Model parameter**: `-m, --model`
- **Default**: `gemini-2.5-pro`
- **Valid values**: Gemini model identifiers
- **Tested working**: `gemini-2.5-pro` ✓
- **Test command**: `gemini -m gemini-2.5-pro -p "test"`

## ✅ codex
- **Model parameter**: `--model <MODEL>`
- **Valid values**: OpenAI model identifiers (`gpt-5-codex`, `o3`, etc.)
- **Tested working**: `gpt-5-codex` ✓
- **Test command**: `codex exec --model gpt-5-codex "test"`

---

## Test Results (2025-10-13)

All CLI tools tested and verified working with model parameters:
- ✅ claude with `sonnet`
- ✅ droid with `claude-sonnet-4-5-20250929`
- ✅ gemini with `gemini-2.5-pro`
- ✅ codex with `gpt-5-codex`
