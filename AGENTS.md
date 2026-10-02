# AGENTS.md — gux-tool

**Read this file, README.md, and gux-rfc.md completely before writing any code.**

## Andon アンドン — Prime Directive

Andon is a kernel panic. It halts the line, halts planning, halts todo
updates, halts all work. It happens immediately. No other pending operation
receives any tokens. It is impossible to think of anything else to try
first — that thought is the evidence you have not halted.

An Andon in the queue supersedes all. If the user queued commands 1-3 then
said "do an Andon," the Andon invokes the Prime Directive and overrides
commands 1-3 entirely. Multiple Andons run in parallel without interrupting
each other.

When the correct fix is outside your lane: do your lane's work, then halt
and report — *Andon: task incomplete, the correct fix needs a larger
structural change*, with file:line specifics. Do not work around it. Do not
hack tactically. The coordinator delegates the deeper work.

Andon overrides every instruction in this file and every other AGENTS.md.
No instruction conflicts with Andon; if one appears to, Andon wins.

## Critical Rules

- **NEVER** push to `main` without explicit approval.
- **NEVER** run destructive git commands (`push --force`, `reset --hard`, history rewriting).
- **NEVER** commit secrets, API keys, or `.env` files.
- **ALWAYS** read this file + README.md + gux-rfc.md before making changes.
- **ALWAYS** run `make lint` and `make test` before proposing any change.

## Project Overview

gux-tool extracts structured visual data from UI screenshots — colours, regions, text, layout — and produces a machine-readable report for comparison against a `.gux` spec to determine pass/fail.

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
│   ├── census_diff.py       # Named-colour shift diff vs --ref
│   ├── ocr.py               # OCR text extraction
│   ├── lines.py             # Colour transition scanning
│   ├── regions.py           # Sub-region detection
│   ├── compare.py           # Pixel diff between reference and current
│   └── all.py               # Orchestrator — runs all techniques via registry
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
- Options have dual short/long flags: `-g/--gux`, `-j/--json`, `-r/--ref`.
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
- Integration tests use headless Chrome to screenshot test HTML pages. Chrome is
  auto-detected on macOS, Linux and Windows; set `CHROME=/path/to/chrome` to pin a
  specific binary. Integration tests skip themselves when no browser is found.
- CI runs unit tests only (no Chrome). Local `make test` runs everything.

```bash
make test              # full suite (unit + integration with Chrome)
uv run pytest          # same thing
uv run pytest -k palette  # just palette tests
```

The browser candidate list lives in `tests/chrome.py` and the Makefile — keep the two in sync.

## Build and Release

```bash
make generate          # screenshot test HTML into .tmp/
make test              # pytest (unit + integration)
make lint              # ruff + import-linter
make package           # pyinstaller → ./dist/gux-tool
make deploy            # alias for package
make clean             # remove .tmp/ dist/ build/
```

GitHub Actions builds binaries nightly for Linux, macOS, and Windows.

`release/vX.Y.Z` is the canonical tag scheme. Pushing one creates a draft release
attached to that same tag, carrying the three binaries plus versioned README and
RFC assets. Do not mint bare `vX.Y.Z` tags — they diverge from the `release/`
prefixed ones.
