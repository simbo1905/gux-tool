# Scoring New Screenshots Against a Calibrated Spec

## When to Use

When the user has a calibrated `.gux` spec and wants to check new screenshots against it. This is the ongoing CI/regression workflow.

## Quick Score (Single Screenshot)

```bash
uv run gux-tool all ./tmp current.png --gux page.gux --fail-on-delta=20
```

Exit code 0 = all zones within tolerance. Exit code 1 = at least one zone exceeded the delta threshold.

## Detailed Report

### Text Output (Human-Readable)

```bash
uv run gux-tool all ./tmp current.png --gux page.gux
```

Shows per-zone: expected vs actual bg, colour delta, transition counts, Assert pass/fail.

### JSON Output (Machine-Readable)

```bash
uv run gux-tool all ./tmp current.png --gux page.gux --json
```

Pipe to `jq` or an LLM for automated analysis.

## Comparative Scoring

### Pixel Diff (Reference vs Current)

```bash
uv run gux-tool compare ./tmp current.png --gux page.gux --ref reference.png
```

Outputs mismatch percentage per zone and saves diff images to `./tmp/`.

### Named Colour Shift (Census Diff)

```bash
uv run gux-tool census-diff ./tmp current.png --gux page.gux --ref reference.png
```

Compares the named-colour distribution between reference and current. Catches "chart disappeared" or "background changed from white to grey" without k-means.

## LLM Verdict

```bash
uv run gux-tool verify ./tmp current.png --gux page.gux --provider groq
```

Runs all extraction, then sends the JSON report + spec to an LLM for per-zone PASS/FAIL with reasons. The LLM never sees pixels.

Supported providers: `groq`, `mistral`, `openai`, or any OpenAI-compatible endpoint.

## CI Integration

### Basic CI Gate

```bash
gux-tool all ./tmp screenshot.png --gux page.gux --fail-on-delta=20 || exit 1
```

### Two-Path Failure Detection

1. **Colour delta** (`--fail-on-delta`): Catches CSS regressions (wrong background, theme leak, style override).
2. **Assert()** in `.gux` spec: Catches structural absence (chart gone blank, table has no rows, content missing).

Both paths are checked independently. A page can pass colour checks but fail Assert (chart area is correct colour but empty).

### Threshold Guidelines

| Threshold | Use Case |
|-----------|----------|
| `--fail-on-delta=5` | Strict: pixel-accurate matching, e.g. brand-critical pages |
| `--fail-on-delta=20` | Standard: catches real regressions, tolerates anti-aliasing and minor rendering differences |
| `--fail-on-delta=50` | Lenient: only catches gross colour changes |

## Interpreting Results

### Zone PASS

- Colour distance < threshold
- All Assert checks met
- Census distribution within expected range

### Zone FAIL: Colour Delta

The dominant colour in the zone has shifted. Common causes:
- CSS class override or specificity change
- Theme/dark-mode leak
- Missing stylesheet (fallback colours)
- Build cache serving stale assets

### Zone FAIL: Assert

The zone lacks expected visual structure. Common causes:
- API returned empty data (chart has no series)
- Component failed to render (JS error)
- Loading state captured instead of loaded state
- Viewport size mismatch (responsive breakpoint)

### Zone FAIL: Census Diff

Named colour distribution shifted significantly. Common causes:
- Chart data changed substantially (expected if data is dynamic)
- Background gradient or image changed
- New UI element overlaying the zone

## Vision-Based Analysis (Optional)

For deeper analysis, send zone crops to a vision LLM:

```bash
uv run gux-tool llm-vision ./tmp current.png --gux page.gux \
    --provider groq --prompt "Does this zone match a dashboard KPI tile?"
```

Use `--prime-rfc` to prepend the GUX RFC for context:

```bash
uv run gux-tool llm-vision ./tmp current.png --gux page.gux \
    --provider groq --prime-rfc \
    --prompt "Does this zone match what the GUX spec describes?"
```
