---
name: gux-visual-regression
description: >-
  This skill should be used when working with GUX visual regression testing,
  .gux spec files, or the gux-tool CLI. This includes writing .gux specs from
  Figma, mockups, wireframes, or verbal descriptions; reverse-engineering .gux
  specs from screenshots, HTML, or PDF; calibrating specs against known-good
  control screenshots; scoring screenshots against baselines; detecting colour
  regressions; detecting structural absence with Assert() thresholds;
  integrating screenshot verification into CI; and working with the gux-tool
  codebase (adding techniques, fixing bugs, running tests). Trigger keywords:
  gux, .gux, gux-tool, visual regression, screenshot verification, colour
  delta, pixel diff, zone extraction, Tailwind colour census, Assert(),
  Bounds(), Style(bg:), census-diff, verify technique, LLM vision.
---

# gux-visual-regression

Visual regression testing for UI screenshots using GUX specs and gux-tool.

GUX is a non-compilable UI description language (baby Dart syntax) that defines the expected visual contract for a screen -- zones, colours, layout, structural assertions. gux-tool extracts structured pixel data from screenshots and compares it against a `.gux` spec. LLMs read the numbers, not the pixels.

## Reference Material

Before working on anything, read these project files:

- `references/gux-rfc.md` -- full GUX language specification (syntax, verification passes, Assert properties, Tailwind shorthand, examples)
- `references/agents.md` -- module architecture, dependency rules, coding conventions, how to add techniques, linting, testing, build/release
- `references/readme.md` -- CLI usage, technique summary, output formats, CI integration, LLM verification

## Capabilities

- Write `.gux` specs from Figma, mockups, wireframes, or verbal descriptions
- Reverse-engineer `.gux` specs from screenshots, HTML, PDF, or Figma exports
- Calibrate specs against known-good control screenshots
- Score new screenshots against calibrated baselines
- Detect colour regressions with configurable delta thresholds (`--fail-on-delta`)
- Detect structural absence (blank charts, empty tables) with `Assert()` thresholds
- Integrate screenshot verification into CI with exit-code gating
- LLM-based per-zone PASS/FAIL verdict (LLM reads extracted numbers, not pixels)

## Techniques

| Technique | Purpose |
|-----------|---------|
| `colours` | Dominant colour extraction per zone (k-means), compares against `Style(bg:)` |
| `zones` | Crop zones by `Bounds()` from spec, save each as PNG |
| `lines` | Colour transition scanning, detects charts/panels/dividers, checks `Assert()` |
| `census` | Map sampled pixels to nearest named Tailwind colour, percentage breakdown |
| `census-diff` | Named colour shift comparison between reference and current images |
| `regions` | Sub-region detection within zones (tiles, cards, cells) |
| `compare` | Pixel diff between reference and current, mismatch percentage + diff image |
| `ocr` | OCR text extraction per zone (opt-in, requires system tesseract) |
| `verify` | Run all + send JSON report to LLM for per-zone pass/fail verdict |
| `llm-vision` | Send zone crop images to a vision LLM (opt-in) |
| `all` | Run all standard techniques (excludes ocr, verify, llm-vision) |

## CLI Quick Reference

```bash
uv run gux-tool <technique> <tmp_dir> <image> [options]
uv run gux-tool all ./tmp ./screenshot.png --gux dashboard.gux --json
uv run gux-tool all ./tmp ./screenshot.png --gux dashboard.gux --fail-on-delta=20
uv run gux-tool census-diff ./tmp ./current.png --gux page.gux --ref ref.png
uv run gux-tool verify ./tmp ./shot.png --gux page.gux --api-key sk-... --provider anthropic
uv run gux-tool rfc          # print the full GUX RFC
uv run gux-tool help         # list all techniques
uv run gux-tool help <name>  # print technique module docstring
```

## GUX Spec Format (Quick Reference)

```dart
import 'gux:core';
import 'gux:tw';

Page('dashboard',
  viewport: Viewport(1280, 800),
  style: Style(bg: tw.white, text: '#0f172a', theme: 'light'),

  Zone('header',
    bounds: Bounds(0, 0, 1280, 60),
    style: Style(bg: '#1e293b', text: tw.white),
  ),

  Zone('chart-area',
    bounds: Bounds(0, 148, 480, 580),
    style: Style(bg: tw.white),
    assert: Assert(min_transitions_v: 10, min_transitions_h: 5),
  ),
)
```

Key constructs:
- `Bounds(x1, y1, x2, y2)` -- pixel coordinates, top-left to bottom-right
- `Style(bg:)` -- expected background colour (hex or `tw.*` shorthand)
- `Assert(min_transitions_v: N)` -- structural presence checks
- `Dynamic('name')` -- marks runtime-variable content
- `///` doc comments -- part of the visual contract
- Any widget name is valid (fictional widgets are first-class)
- Imports are intent markers, not real packages

## Development Workflow

To modify the gux-tool codebase, always read `references/agents.md` first. Key commands:

```bash
make lint              # ruff check + format check + lint-imports
make test              # full test suite (unit + integration)
uv run pytest -k name  # run specific tests
make package           # pyinstaller -> ./dist/gux-tool
```
