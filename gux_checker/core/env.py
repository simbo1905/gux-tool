"""Environment variable loading for gux-tool.

Load order (first wins):
  1. Existing OS environment variables — never overwrite.
  2. .env file at --env-file path (if explicitly provided).
  3. .env file walking up from cwd, stopping at .git (file or dir).

Walking stops at .git so we never load a .env from outside the repo.
Only sets variables that are NOT already in os.environ.
"""

import os
from pathlib import Path


def _find_dotenv(start: Path) -> Path | None:
    """Walk up from start, return first .env found, stop at .git boundary."""
    current = start.resolve()
    while True:
        candidate = current / '.env'
        if candidate.is_file():
            return candidate
        # Stop at repo root — .git can be a dir (normal clone) or file (worktree)
        if (current / '.git').exists():
            return None
        parent = current.parent
        if parent == current:
            # Filesystem root — give up
            return None
        current = parent


def _parse_dotenv(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict. Handles KEY=value and KEY="value"."""
    result: dict[str, str] = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, _, raw_value = line.partition('=')
        key = key.strip()
        value = raw_value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def load_env(env_file: str | None = None) -> Path | None:
    """Load .env into os.environ for keys not already set.

    Returns the path that was loaded, or None if no .env was found/used.
    """
    if env_file:
        path = Path(env_file)
        if not path.is_file():
            return None
    else:
        path = _find_dotenv(Path.cwd())
        if path is None:
            return None

    parsed = _parse_dotenv(path)
    for key, value in parsed.items():
        if key not in os.environ:
            os.environ[key] = value

    return path
