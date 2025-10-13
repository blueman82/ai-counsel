# CLI Model Reference

Quick reference for model parameters accepted by each CLI tool.

## claude
- **Model parameter**: `--model <model>`
- **Valid values**: Aliases like `sonnet`, `opus`, `haiku` or full names like `claude-sonnet-4-5-20250929`
- **Example**: `sonnet`

## droid
- **Model parameter**: `-m, --model <id>`
- **Default**: `gpt-5-codex`
- **Valid values**: Any model ID supported by droid
- **Example**: `sonnet4.5`

## gemini
- **Model parameter**: `-m, --model`
- **Default**: `gemini-2.5-pro`
- **Valid values**: Gemini model identifiers
- **Example**: `gemini-2.5-pro`

## codex
- **Model parameter**: `-m, --model <MODEL>`
- **Valid values**: OpenAI model identifiers
- **Example**: `gpt-5-codex` or `o3`
