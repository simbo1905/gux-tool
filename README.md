# gux-tool

Visual regression testing for UI screenshots using [GUX specs](./gux-rfc.md).

Extracts structured data from screenshot pixels — colours, regions, text, layout — and produces a machine-readable report that an LLM can compare against a `.gux` spec to determine pass/fail. The LLM never sees the pixels. It reads numbers.

## Install

```bash
# From source
uv run gux-tool --help

# Or build a standalone binary
uv run pyinstaller gux_checker/__main__.py -n gux-tool --onefile
./dist/gux-tool --help
```

## Quick Start

```bash
# Run all techniques against a screenshot, output to a temp folder
uv run gux-tool all ./tmp ./screenshot.png

# Run a single technique
uv run gux-tool colours ./tmp ./screenshot.png

# Run with a .gux spec (extracts zones by bounds)
uv run gux-tool all ./tmp ./screenshot.png --gux dashboard.gux

# Get JSON output for piping to an LLM
uv run gux-tool all ./tmp ./screenshot.png --gux dashboard.gux --json

# CI gate: fail if any zone colour delta exceeds threshold
uv run gux-tool all ./tmp ./screenshot.png --gux dashboard.gux --fail-on-delta=20

# Compare named colour shifts between ref and current
uv run gux-tool census-diff ./tmp ./current.png --gux page.gux --ref ref.png

# Ask an LLM to verify (requires API key)
uv run gux-tool verify ./tmp ./screenshot.png --gux dashboard.gux --api-key sk-...
```

## Techniques

Each technique is a self-contained Python module that extracts one kind of information from the screenshot. Run `uv run gux-tool <technique> --help` for details.

| Technique | What it does |
|-----------|-------------|
| `colours` | Dominant colour extraction per zone (k-means). Colour census against named Tailwind palette. Percentage breakdown. |
| `zones` | Crop zones by `Bounds(...)` from the `.gux` spec. Save each as a separate PNG in the temp folder. |
| `lines` | Sample horizontal and vertical pixel rows. Find colour transitions — panel edges, dividers, borders, input outlines. Checks `Assert()` thresholds from `.gux` specs. |
| `census` | Map every sampled pixel to nearest named colour from the spec's palette. Output percentages per zone. |
| `census-diff` | Compare named colour shifts between reference and current screenshot. Requires `--ref`. Catches "chart disappeared" without k-means. |
| `regions` | Subdivide zones into sub-regions by detecting colour boundaries. Find tiles within tile rows, cards within grids. |
| `compare` | Pixel-diff two images (reference vs current). Output mismatch percentage per zone and a diff image. |
| `ocr` | OCR each zone. Extract text, bounding boxes, confidence scores. **Opt-in only** — requires system `tesseract-ocr`. Not included in `all`. |
| `all` | Run every technique (except `ocr` and `verify`). Combine into a single report. |
| `verify` | Run `all`, then send the report + `.gux` spec to an LLM API for pass/fail verdict. **Opt-in only** — requires API key. |

### Adding a technique

Create `gux_checker/techniques/my_technique.py`:

```python
"""One-line description shown in --help."""

from gux_checker.types import Technique, ZoneImage, Report

technique = Technique(
    name='my_technique',
    help='Longer description for --help',
)

@technique.run
def run(zone: ZoneImage, report: Report, args) -> None:
    # Do your pixel analysis on zone.image (PIL.Image)
    # Write results to report
    report.add(zone.name, 'my_metric', {'value': 42})
    # Optionally save artefacts to args.tmp_dir
```

It auto-registers. No other wiring needed.

## Output

### Text (default)

```
gux-tool: ./screenshot.png (920×910) — dashboard.gux (6 zones)

── toolbar [0,0→960,45]
  bg: expected #ffffff  got #ffffff  Δ=0.0  ✓
  text: ['Sonar', '—', 'Margin', 'Monitor', 'Standard', '0-60%']
  transitions: h=4.2 v=1.8 avg/line

── kpi-tiles [0,55→960,140]
  bg: expected #ffffff  got #ffffff  Δ=0.0  ✓
  text: ['Avg', 'Margin', '(Fee)', '149', 'bps', 'Threshold', '100']
  sub-regions: 4 panels detected (white bg, bordered)

── net-margin-chart [0,148→480,580]
  bg: expected #ffffff  got #ffffff  Δ=0.0  ✓
  content: non-blank ✓ (5 dominant colours, chart-like distribution)
  text: ['Net', 'Margin', 'by', 'Tier', 'Fee', 'Fee Assisted', 'LM1', 'LM2']

PASS 5/6 zones  FAIL 1/6 zones
```

### JSON (`--json`)

```json
{
  "image": "./screenshot.png",
  "dimensions": {"width": 920, "height": 910},
  "gux": "dashboard.gux",
  "zones": [
    {
      "name": "toolbar",
      "bounds": [0, 0, 960, 45],
      "techniques": {
        "colours": {
          "dominant": [{"hex": "#ffffff", "pct": 82.1, "nearest": "white"}],
          "expected_bg": "#ffffff",
          "actual_bg": "#ffffff",
          "distance": 0.0,
          "pass": true
        },
        "ocr": {
          "texts": ["Sonar", "—", "Margin", "Monitor"],
          "detail": [{"text": "Sonar", "x": 20, "y": 12, "conf": 96}]
        },
        "lines": {
          "h_avg_transitions": 4.2,
          "v_avg_transitions": 1.8
        }
      }
    }
  ],
  "summary": {"total": 6, "pass": 5, "fail": 1}
}
```

## LLM Verification (`verify`)

The `verify` technique runs all extraction, then sends the JSON report + the `.gux` spec text to an LLM and asks it to compare. The prompt is:

> Here is a GUX visual spec and a structured extraction report from a screenshot.
> Compare each zone's extracted data against the spec.
> For each zone, state PASS or FAIL with a one-line reason.
> Do not ask for the image. All the data you need is in the report.

Supported providers via `--provider`:

- `anthropic` (default) — Claude Sonnet
- `openai` — GPT-4o-mini

```bash
uv run gux-tool verify ./tmp ./shot.png --gux page.gux \
    --api-key sk-ant-... --provider anthropic
```

## GUX Spec Format

See [gux-rfc.md](./gux-rfc.md) for the full specification.

Short version: it's baby Dart. Widget tree syntax, fictional widgets, `Bounds(x1,y1,x2,y2)` for zone coordinates, `Style(bg: '#ffffff')` for expected colours, `///` doc comments for intent.

```dart
import 'gux:core';
import 'gux:tw';

Page('my-page',
  viewport: Viewport(1280, 800),
  style: Style(bg: tw.white),

  Zone('header',
    bounds: Bounds(0, 0, 1280, 60),
    style: Style(bg: '#1e293b', text: tw.white),
    children: [ Title('My App') ],
  ),
)
```

## CI Integration

Use `--fail-on-delta=N` to gate CI pipelines. If any zone's dominant colour distance exceeds `N`, `gux-tool` exits with code 1.

```bash
gux-tool all ./tmp screenshot.png --gux page.gux --fail-on-delta=20 || echo "REGRESSION"
```

Two separate failure paths:
- **Colour Δ** (`--fail-on-delta`) — catches CSS regressions (wrong background, theme leak)
- **Assert()** in `.gux` specs — catches structural absence (chart gone blank, table has no rows)

## Requirements

- Python 3.11+
- `uv` for running / building
- Optional: `tesseract-ocr` (for `ocr` technique only)
- Optional: Anthropic or OpenAI API key (for `verify` technique)

## License

MIT
