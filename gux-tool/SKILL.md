---
name: gux-visual-regression
description: >-
  This skill should be used when users need GUX visual regression outcomes:
  decide whether a UI screenshot matches intent, create or refine .gux specs,
  run gux-tool checks, and gate regressions in CI. This skill is a signpost to
  the release assets (binary, versioned README, versioned RFC), not a duplicate
  of those docs. Trigger keywords: gux, .gux, gux-tool, screenshot
  verification, visual regression, colour delta, pixel diff, zone extraction,
  Assert(), Bounds(), Style(bg:), census-diff, verify.
---

# gux-visual-regression

Use this skill as a high-level guide for **intent, objectives, and outcomes**.

Do not duplicate full tool documentation in this file. Read the release assets for exact behavior and command details.

## Intent

- Decide if `gux-tool` is the right tool for the task.
- If yes, install and run the release binary safely.
- Use the version-matched README and RFC from the same release for all detailed behavior.

## Objectives

- Produce machine-checkable visual assertions from screenshots.
- Compare screenshot reality to a `.gux` visual contract.
- Detect both colour regressions and structural absence.
- Support CI pass/fail gating.

## Outcomes

- Clear per-zone PASS/FAIL evidence.
- Reproducible checks tied to a specific binary + RFC + README version.
- Fast go/no-go decision for visual changes.

## Install from latest release (minimal flow)

Release page:

- `https://github.com/simbo1905/gux-tool/releases/latest`

From the latest release, download the matching assets for your platform/version:

- binary: `gux-tool-${os}-${arch}` (or `.exe` on Windows)
- versioned RFC asset
- versioned README asset

### macOS quarantine removal

If running on macOS, remove quarantine before first run:

```bash
xattr -d com.apple.quarantine ./gux-tool-macos-arm64
```

(Use the matching macOS filename if not arm64.)

### Version compatibility check

After download, verify what the binary is built for:

```bash
./gux-tool-${os}-${arch} rfc
```

## Decision gate (use / don’t use)

Use this skill when the task needs visual-contract checks from screenshots.

Do not use this skill when the task is purely DOM/unit logic with no screenshot-based verification.

## Where detailed behavior lives

Use release-matched docs (same tag as the binary):

- versioned README asset: complete CLI/technique usage
- versioned RFC asset: exact GUX language/spec semantics

If the release assets are unavailable for the required platform, build from source and then use `./dist/gux-tool rfc` to confirm alignment.
