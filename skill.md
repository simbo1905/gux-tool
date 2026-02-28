# gux-visual-regression

Visual regression testing for UI screenshots using GUX specs and gux-tool.

GUX is a non-compilable UI description language (baby Dart syntax) that defines the expected visual contract for a screen — zones, colours, layout, structural assertions. gux-tool extracts structured pixel data from screenshots and compares it against a `.gux` spec. LLMs read the numbers, not the pixels.

Full documentation: [skills/gux-visual-regression/skill-full.md](./skills/gux-visual-regression/skill-full.md)

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

- `colours` — dominant colour extraction per zone (k-means), compares against `Style(bg:)`
- `zones` — crop zones by `Bounds()` from spec, save each as PNG
- `lines` — colour transition scanning, detects charts/panels/dividers, checks `Assert()`
- `census` — map sampled pixels to nearest named Tailwind colour, percentage breakdown
- `census-diff` — named colour shift comparison between reference and current images
- `regions` — sub-region detection within zones (tiles, cards, cells)
- `compare` — pixel diff between reference and current, mismatch percentage + diff image
- `ocr` — OCR text extraction per zone (opt-in, requires system tesseract)
- `verify` — run all + send JSON report to LLM for per-zone pass/fail verdict
- `llm-vision` — send zone crop images to a vision LLM (opt-in)
- `all` — run all standard techniques (excludes ocr, verify, llm-vision)

## Tooling

- CLI: `uv run gux-tool <technique> <tmp_dir> <image> [options]`
- Spec format: baby Dart widget tree syntax, `.gux` file extension, never compiles
- Colour palette: full Tailwind `tw.*` shorthand plus hex values
- LLM providers: groq, mistral, openai, or any OpenAI-compatible endpoint
- CI gate: `--fail-on-delta=N` exits 1 when any zone colour distance exceeds N
- Two independent failure paths: colour delta AND structural Assert checks

## Spec Format (summary)

```dart
Page('name', viewport: Viewport(1280, 800),
  Zone('header', bounds: Bounds(0, 0, 1280, 60), style: Style(bg: '#1e293b')),
)
```

- `Bounds(x1, y1, x2, y2)` — pixel coordinates, top-left to bottom-right
- `Style(bg:)` — expected background colour (hex or `tw.*` shorthand)
- `Assert(min_transitions_v: N)` — structural presence checks
- `Dynamic('name')` — marks runtime-variable content
- `///` doc comments — part of the visual contract
- Any widget name is valid (fictional widgets are first-class)

## GUX Spec Language

- Imports are intent markers, not real packages
- `import 'gux:tw'` — enables Tailwind shorthand
- `import 'gux:charts'` — signals chart widget usage
- `import 'gux:controls'` — signals control widget usage
- Full RFC: `uv run gux-tool rfc`
