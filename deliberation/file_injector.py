"""Resolve file paths/globs and inject contents into prompts."""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default from config, can be overridden
DEFAULT_MAX_BYTES = 512_000  # 500KB

# Patterns to always exclude (matches tool_security.exclude_patterns)
EXCLUDE_DIRS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'transcripts'}


def resolve_files(patterns: list[str], working_directory: str) -> list[Path]:
    """Resolve file paths and glob patterns to concrete file paths.

    Args:
        patterns: List of file paths or glob patterns
        working_directory: Base directory for resolving relative paths

    Returns:
        Deduplicated, sorted list of resolved file paths
    """
    base = Path(working_directory)
    resolved = set()

    for pattern in patterns:
        # Check if it's a glob pattern
        if any(c in pattern for c in ['*', '?', '[']):
            matches = list(base.glob(pattern))
            if not matches:
                logger.warning(f"File pattern matched nothing: {pattern}")
            for match in matches:
                if match.is_file() and not _is_excluded(match):
                    resolved.add(match.resolve())
        else:
            # Explicit path
            path = base / pattern
            if path.is_file():
                resolved.add(path.resolve())
            else:
                logger.warning(f"File not found: {pattern} (resolved to {path})")

    return sorted(resolved)


def _is_excluded(path: Path) -> bool:
    """Check if a file path should be excluded."""
    parts = path.parts
    return any(excluded in parts for excluded in EXCLUDE_DIRS)


def _is_binary(path: Path) -> bool:
    """Quick check if a file appears to be binary."""
    try:
        with open(path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except Exception:
        return True


def inject_file_contents(
    prompt: str,
    patterns: list[str],
    working_directory: str,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> str:
    """Resolve files and prepend their contents to the prompt.

    Args:
        prompt: Original deliberation prompt
        patterns: File paths or glob patterns
        working_directory: Base directory for resolving
        max_bytes: Maximum total bytes to inject

    Returns:
        Prompt with file contents prepended
    """
    files = resolve_files(patterns, working_directory)

    if not files:
        logger.info("No files resolved from patterns, using prompt as-is")
        return prompt

    sections = []
    total_bytes = 0

    for path in files:
        if _is_binary(path):
            logger.warning(f"Skipping binary file: {path}")
            continue

        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning(f"Skipping file with encoding error: {path}")
            continue
        except Exception as e:
            logger.warning(f"Error reading {path}: {e}")
            continue

        content_bytes = len(content.encode('utf-8'))
        if total_bytes + content_bytes > max_bytes:
            logger.warning(
                f"File injection limit reached ({max_bytes} bytes). "
                f"Skipping {path} and remaining files."
            )
            break

        # Use relative path for display
        try:
            display_path = path.relative_to(Path(working_directory).resolve())
        except ValueError:
            display_path = path.name

        sections.append(f"--- File: {display_path} ---\n{content}")
        total_bytes += content_bytes

    if not sections:
        return prompt

    logger.info(f"Injected {len(sections)} files ({total_bytes:,} bytes) into prompt")

    file_block = "\n\n".join(sections)
    return f"{file_block}\n\n---\n\n{prompt}"
