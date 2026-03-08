---
name: gux-visual-regression
description: >-
  This skill should be used when users need GUX visual regression work:
  writing or reviewing .gux specs, running gux-tool techniques, calibrating
  screenshot baselines, checking colour/structure regressions, and integrating
  screenshot checks into CI. This skill also covers installing gux-tool from
  GitHub Releases with checksum verification and platform-specific setup.
  Trigger keywords: gux, .gux, gux-tool, visual regression, screenshot,
  screenshot verification, colour delta, pixel diff, zone extraction,
  Tailwind colour census, Bounds(), Style(bg:), Assert(), census-diff,
  verify, llm-vision.
---

# gux-visual-regression

Use this skill for GUX spec authoring, screenshot verification, and gux-tool operations.

## Reference Material (read first)

Before starting implementation or debugging, read:

- `../references/gux-rfc.md` -- authoritative GUX language spec and examples
- `../references/agents.md` -- module architecture, dependency rules, coding conventions
- `../references/readme.md` -- CLI usage, output formats, CI patterns, technique overview

## Capabilities

- Write `.gux` specs from Figma, mockups, wireframes, or verbal descriptions
- Reverse-engineer `.gux` specs from screenshots, HTML, PDF, or Figma exports
- Calibrate specs against known-good control screenshots
- Score new screenshots against calibrated baselines
- Detect colour regressions with configurable delta thresholds (`--fail-on-delta`)
- Detect structural absence (blank charts, empty tables) with `Assert()` thresholds
- Integrate screenshot verification into CI with exit-code gating
- LLM-based per-zone PASS/FAIL verification from structured extraction data

## Install gux-tool from latest GitHub Release (critical)

Release page:

- `https://github.com/simbo1905/gux-tool/releases/latest`

Pick the correct binary for OS/arch:

- macOS Apple Silicon: `gux-tool-macos-arm64`
- macOS Intel: `gux-tool-macos-x64`
- Linux x64: `gux-tool-linux-x64`
- Windows x64: `gux-tool-windows-x64.exe`

### 1) Download binary and checksum file

Download both:

- the binary for the current OS/arch
- the SHA256 checksum file published in the same release assets

### 2) Verify SHA256 before execution

Use OS-native checksum validation.

macOS/Linux:

```bash
shasum -a 256 ./gux-tool-${os}-${arch}
# Compare output manually with release SHA256 entry for that exact filename
```

Linux alternative:

```bash
sha256sum ./gux-tool-${os}-${arch}
```

Windows PowerShell:

```powershell
Get-FileHash .\gux-tool-${os}-${arch}.exe -Algorithm SHA256
```

### 3) macOS quarantine removal (required on downloaded binaries)

If and only if running macOS, execute:

```bash
xattr -d com.apple.quarantine ./gux-tool-macos-arm64
```

(Use the matching macOS filename if not arm64.)

### 4) Confirm embedded GUX RFC/version compatibility

Run:

```bash
./gux-tool-${os}-${arch} rfc
```

This is the authoritative check for the exact GUX RFC/version baked into that binary.

## Build from source (fallback when binary is unavailable)

If OS/arch binary is unavailable, build from source:

```bash
uv run pyinstaller gux_checker/__main__.py -n gux-tool --onefile
./dist/gux-tool rfc
```

## Runtime quick commands

```bash
uv run gux-tool help
uv run gux-tool help <technique>
uv run gux-tool rfc
uv run gux-tool all ./tmp ./screenshot.png --gux page.gux --json
uv run gux-tool all ./tmp ./screenshot.png --gux page.gux --fail-on-delta=20
uv run gux-tool census-diff ./tmp ./current.png --gux page.gux --ref ref.png
uv run gux-tool verify ./tmp ./screenshot.png --gux page.gux --api-key <key> --provider anthropic
```

## GUX spec template (copy/paste baseline)

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

Quick reminders:

- `Bounds(x1, y1, x2, y2)` defines pixel crop zones
- `Style(bg:)` sets expected background colour (`#hex` or `tw.*`)
- `Assert(...)` enforces structural presence thresholds
- `Dynamic('name')` marks runtime-variable values
- `///` comments are part of the visual contract

## Technique inventory

| Technique | Purpose |
|-----------|---------|
| `colours` | Dominant colour extraction per zone (k-means), compared against `Style(bg:)` |
| `zones` | Zone cropping from `Bounds()` and zone image export |
| `lines` | Colour transition scanning for structural content checks (`Assert`) |
| `census` | Pixel-to-nearest-named-colour mapping with percentages |
| `census-diff` | Named-colour shift comparison between reference and current screenshots |
| `regions` | Sub-region detection (tiles/cards/cells) within a zone |
| `compare` | Pixel diff between reference and current, with mismatch percentage |
| `ocr` | OCR text extraction per zone (opt-in, requires system tesseract) |
| `llm-vision` | Zone image analysis via vision LLM (opt-in) |
| `verify` | Run extraction and request LLM pass/fail verdict by zone (opt-in) |
| `all` | Run all standard techniques; excludes `ocr`, `llm-vision`, `verify` |
