---
name: gux-visual-regression
description: "Visual regression testing for UI screenshots using GUI UX Description Language GUX specs and gux-tool. This skill should be used when writing .gux spec files from designs or mockups, reverse-engineering .gux specs from existing screenshots or HTML pages, calibrating specs against reference screenshots, scoring new screenshots for visual regressions, setting up CI gates for screenshot testing, comparing pixel diffs or colour census between reference and current images, or using LLM-based verification of UI screenshots against a visual contract. Covers the GUX spec format (baby-Dart widget tree syntax), gux-tool CLI techniques (colours, zones, lines, census, census-diff, regions, compare, ocr, verify, llm-vision), Tailwind colour palettes, Assert thresholds, and the full authoring-to-CI workflow."
---

# GUX Visual Regression

## Overview

GUX is a UI description language (baby Dart pseudo-code) that gives humans and LLMs a shared contract for what a screen should look like. `gux-tool` extracts structured data from screenshot pixels and compares it against a `.gux` spec. The LLM never sees pixels -- it reads numbers. To use this tool you MUST be able to screenshot your screens - you can do this manually or you can use automation tools such as headless chrome, kapture, Playwright or puppeteer. 

## Workflow Decision Tree

Determine which workflow to follow based on the user's situation:

- **Has a design, needs a spec** -> Read `references/writing-gux.md`
- **Has an existing UI, needs a spec** -> Read `references/reverse-engineering.md`
- **Has a spec + reference screenshot, needs to calibrate** -> Read `references/calibration.md`
- **Has a calibrated spec, needs to check new screenshots** -> Read `references/scoring.md`

## Tool Reference

`gux-tool` runs as: `uv run gux-tool <technique> <tmp_dir> <image> [options]`

### Techniques

| Technique | Purpose |
|-----------|---------|
| `colours` | Dominant colour extraction per zone (k-means). Compares against expected `Style(bg:)`. |
| `zones` | Crop zones by `Bounds()` from the spec. Save each as separate PNG. |
| `lines` | Colour transition scanning. Detects structure (charts, tables, panels). Checks `Assert()`. |
| `census` | Map sampled pixels to nearest named Tailwind colour. Percentage breakdown. |
| `census-diff` | Compare named colour shifts between reference and current. Requires `--ref`. |
| `regions` | Detect sub-regions within zones (tiles, cards, cells). |
| `compare` | Pixel diff between reference and current. Mismatch percentage + diff image. |
| `ocr` | OCR text extraction. Opt-in only, requires system `tesseract-ocr`. |
| `llm-vision` | Send zone crops to a vision LLM. Opt-in, requires API key. |
| `all` | Run all standard techniques (except `ocr`, `verify`, `llm-vision`). |
| `verify` | Run `all` + send report to LLM for per-zone PASS/FAIL verdict. |

### Common Options

| Flag | Short | Purpose |
|------|-------|---------|
| `--gux FILE` | `-g` | Path to `.gux` spec file |
| `--json` | `-j` | Output JSON instead of text |
| `--ref IMAGE` | `-r` | Reference image for compare/census-diff |
| `--fail-on-delta N` | `-d` | Exit 1 if any zone colour distance exceeds N |
| `--api-key KEY` | `-k` | LLM API key (overrides env var) |
| `--provider NAME` | `-p` | LLM provider: groq, mistral, openai, or any OpenAI-compatible |

### Provider Configuration

Set env vars (or use `.env` file):

```
{PROVIDER}_API_KEY    required
{PROVIDER}_API_URL    required (has defaults for groq, mistral, openai)
{PROVIDER}_MODEL      optional override
```

Built-in defaults:
- `groq`: llama-3.3-70b-versatile at api.groq.com
- `mistral`: mistral-medium-2505 at api.mistral.ai
- `openai`: gpt-4o-mini at api.openai.com

## GUX Spec Quick Reference

A `.gux` file describes one page using Flutter/Dart widget tree syntax. It never compiles or executes.

```dart
import 'gux:core';
import 'gux:tw';

Page('page-name',
  viewport: Viewport(1280, 800),
  style: Style(bg: tw.white, text: '#0f172a', theme: 'light'),

  Zone('header',
    bounds: Bounds(0, 0, 1280, 60),
    style: Style(bg: '#1e293b', text: tw.white),
    children: [ Title('My App') ],
  ),

  Zone('chart',
    bounds: Bounds(0, 60, 640, 500),
    style: Style(bg: tw.white),
    assert: Assert(min_transitions_v: 10),
    children: [ BarChart(series: Dynamic('data')) ],
  ),
)
```

Key rules:
- `Bounds(x1, y1, x2, y2)` -- top-left to bottom-right, pixels.
- `Style(bg:)` accepts hex `'#ffffff'` or Tailwind shorthand `tw.white`.
- `Assert()` checks structural presence (transitions, regions, non_blank).
- `Dynamic('name')` marks runtime-variable content.
- `///` doc comments are part of the contract.
- Any widget name is valid (fictional widgets are first-class).

For the full GUX specification, run `uv run gux-tool rfc`.

## Resources

### references/

| File | When to read |
|------|-------------|
| `writing-gux.md` | Authoring a `.gux` spec from a design, mockup, or description |
| `reverse-engineering.md` | Extracting a `.gux` spec from an existing screenshot, HTML, PDF, or Figma |
| `calibration.md` | Tuning a spec against a known-good reference screenshot |
| `scoring.md` | Checking new screenshots against a calibrated spec, CI integration |
