# AGENTS.md — gux-tool

**Read this file, README.md, and gux-rfc.md completely before writing any code.**

## Critical Rules

- **NEVER** push to `main` without explicit approval.
- **NEVER** run destructive git commands (`push --force`, `reset --hard`, history rewriting).
- **NEVER** commit secrets, API keys, or `.env` files.
- **ALWAYS** read this file + README.md + gux-rfc.md before making changes.
- **ALWAYS** run `make lint` and `make test` before proposing any change.

## Project Overview

gux-tool extracts structured visual data from UI screenshots — colours, regions, text, layout — and produces a machine-readable report. An LLM can compare that report against a `.gux` spec to determine pass/fail. The LLM never sees pixels. It reads numbers.

The tool runs as: `uv run gux-tool <technique> <tmp_dir> <image> [options]`

## Module Architecture

```
gux_checker/
├── core/                    # Foundation layer — stdlib + numpy + PIL only
│   ├── palette.py           # Tailwind colour map + RGB distance functions
│   ├── types.py             # Technique, ZoneImage, Report, GuxZone, GuxSpec
│   ├── gux_parser.py        # Regex-based .gux parser
│   └── report.py            # Text + JSON report builder
├── techniques/              # Each module is independent — cannot import other techniques
│   ├── zones.py             # Crop zones by Bounds, save PNGs
│   ├── colours.py           # Dominant colour extraction (k-means)
│   ├── census.py            # Pixel-to-named-colour census
│   ├── ocr.py               # OCR text extraction
│   ├── lines.py             # Colour transition scanning
│   ├── regions.py           # Sub-region detection
│   ├── compare.py           # Pixel diff between reference and current
│   ├── all.py               # Orchestrator — runs all techniques via registry
│   └── verify.py            # Orchestrator — runs all + sends to LLM
├── registry.py              # Auto-discovery of technique modules
├── __init__.py
└── __main__.py              # CLI entry point (can import anything)
bin/
└── gux-tool              # Standalone uv run --script wrapper
```

### Dependency Rules

| Module | Can Import From | Cannot Import From |
|--------|-----------------|-------------------|
| `gux_checker.core` | stdlib, numpy, PIL | `techniques`, `registry`, `__main__` |
| `gux_checker.techniques.*` | `gux_checker.core`, numpy, PIL | other techniques, `__main__` |
| `gux_checker.techniques.all` | `gux_checker.core`, `gux_checker.registry` | other techniques directly |
| `gux_checker.techniques.verify` | `gux_checker.core`, `gux_checker.registry` | other techniques directly |
| `gux_checker.registry` | `gux_checker.core`, `gux_checker.techniques` (scan only) | `__main__` |
| `gux_checker.__main__` | anything | — |

These rules are **enforced by import-linter** via `uv run lint-imports`. Pre-commit hooks run this on every commit.

## How to Add a New Technique

1. Create `gux_checker/techniques/my_technique.py`
2. Write a **module docstring** — this becomes the documentation (printed by `gux-tool help my-technique`)
3. Define a `technique` object and a `@technique.run` decorated function:

```python
"""Short description shown in --help.

Longer description printed by `gux-tool help my-technique`.
Explain what it does, what it outputs, and give an example command.

Example:
    uv run gux-tool my-technique ./tmp screenshot.png --gux page.gux
"""

from gux_checker.core.types import Technique, ZoneImage, Report

technique = Technique(
    name='my_technique',
    help='Short description for --help',
)

@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    for zone in zones:
        # Analyse zone.image (PIL.Image)
        report.add(zone.name, 'my_technique', {'value': 42})
```

4. It auto-registers. No other wiring needed. The CLI discovers it, adds a subcommand, and `help my-technique` prints the module docstring.

## Coding Conventions

### General
- Follow [PEP 8](https://peps.python.org/pep-0008/). Long lines are fine (limit 120).
- Type hint all function signatures (`def foo(x: int) -> str:`).
- Use f-strings, not `.format()` or concatenation.
- Write simple verbose code rather than complex one-liners.
- Keep functions under 30 lines where possible.
- Use meaningful variable names.

### Classes
- Classes serve **only** as namespaces to group related functionality.
- ALL methods MUST be `@staticmethod`.
- NEVER use instance methods or `__init__` for logic classes.
- Use `@dataclass` for data containers only.
- Constants are class attributes with `Final` type hints.

### Data Types
- Prefer built-in types: `int`, `float`, `str`, `bool`, `list`, `dict`, `tuple`.
- Use `int | None` not `Optional[int]`.
- ALL functions MUST have complete type annotations.

### Error Handling
- Be specific: `except ValueError`, not `except Exception`.

### Imports
- Use absolute imports: `from gux_checker.core.palette import hex_to_rgb`.
- Group: 1) stdlib, 2) third-party, 3) local.

### Documentation
- Module docstrings are mandatory — they drive the CLI help system.
- Comments describe intent, not what the code does.

## CLI Conventions

- ALL commands support `-h` and `--help`.
- Options have dual short/long flags: `-g/--gux`, `-j/--json`, `-k/--api-key`, `-p/--provider`, `-r/--ref`.
- `gux-tool help` lists all techniques with short descriptions.
- `gux-tool help <technique>` prints the full module docstring.

## Linting and Hooks

### Tools (configured in pyproject.toml)
- **ruff** — linting + formatting (replaces black, isort, flake8)
- **import-linter** — enforces module dependency architecture
- **mypy** — type checking (optional deps have `ignore_missing_imports`)

### Pre-commit hooks (.pre-commit-config.yaml)
- `check-yaml`, `end-of-file-fixer`, `trailing-whitespace`
- `ruff --fix --unsafe-fixes`, `ruff-format`
- `uv run lint-imports`

### Running manually
```bash
make lint              # ruff check + format check + lint-imports
uv run ruff check .    # just lint
uv run ruff format .   # just format
uv run lint-imports    # just architecture check
```

## Testing

- Use `pytest`. Test files match modules: `test_palette.py` tests `palette.py`.
- Test function names: `test_<function_name>` or `test_<function_name>_<variation>`.
- Use `@pytest.mark.parametrize` for multiple inputs.
- Do NOT bundle large binary fixtures. Generate test data programmatically.
- Integration tests use headless Chrome to screenshot test HTML pages.
- CI runs unit tests only (no Chrome). Local `make test` runs everything.

```bash
make test              # full suite (unit + integration with Chrome)
uv run pytest          # same thing
uv run pytest -k palette  # just palette tests
```

## Build and Release

```bash
make generate          # screenshot test HTML into .tmp/
make test              # pytest (unit + integration)
make lint              # ruff + import-linter
make package           # pyinstaller → ./dist/gux-tool
make deploy            # alias for package
make clean             # remove .tmp/ dist/ build/
```

GitHub Actions builds binaries nightly for Linux, macOS, and Windows. Tag `release/vX.Y.Z` creates a draft release with all three binaries attached.
