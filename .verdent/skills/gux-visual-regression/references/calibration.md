# Calibrating a GUX Spec Against Control Samples

## When to Use

When the user has a `.gux` spec and a known-good screenshot (the "reference" or "control") and wants to tune the spec so that it passes cleanly. This is the step between writing a spec and deploying it in CI.

## Workflow

### Step 1: Run Full Extraction

```bash
uv run gux-tool all ./tmp reference.png --gux page.gux --json > baseline.json
```

Examine the output for each zone:
- `distance`: colour delta between expected and actual. Should be < 5.0 for a well-calibrated spec.
- `h_avg_transitions` / `v_avg_transitions`: transition counts for Assert checks.
- `dominant`: the actual dominant colours found.

### Step 2: Fix Colour Mismatches

If a zone shows `distance: 7.3` with `expected_bg: #ffffff` and `actual_bg: #f8fafc`:

Option A: Update the spec to match reality.
```dart
style: Style(bg: '#f8fafc'),  // was #ffffff, actual render uses slate-50
```

Option B: Accept the delta if it's within tolerance. The default `--fail-on-delta` threshold is configurable.

### Step 3: Tune Assert Thresholds

Run the `lines` technique to see actual transition counts:
```bash
uv run gux-tool lines ./tmp reference.png --gux page.gux --json
```

For a chart zone showing `h_avg_transitions: 12.4, v_avg_transitions: 8.7`:
```dart
assert: Assert(min_transitions_h: 5, min_transitions_v: 4),
// Thresholds set well below actual values to allow for data variation
```

Rule of thumb: set Assert thresholds at ~40-50% of the measured values from the reference. This accommodates data variation without missing structural absence.

### Step 4: Verify Zone Bounds

Run the `zones` technique to see cropped images:
```bash
uv run gux-tool zones ./tmp reference.png --gux page.gux
ls ./tmp/
```

Visually inspect each cropped zone PNG in `./tmp/`. Check that:
- Each crop contains only the intended content.
- No zone includes borders or padding from adjacent zones.
- Chart zones crop the chart area, not just white space around it.

### Step 5: Run Census for Colour Distribution

```bash
uv run gux-tool census ./tmp reference.png --gux page.gux --json
```

Census maps every sampled pixel to a named Tailwind colour. Use this to:
- Confirm the dominant colour matches `Style(bg:)`.
- Identify unexpected colours that might indicate rendering issues.
- Establish baseline colour distributions for `census-diff` later.

### Step 6: CI Gate Test

Run with `--fail-on-delta` at the threshold you plan to use in CI:
```bash
uv run gux-tool all ./tmp reference.png --gux page.gux --fail-on-delta=20
echo $?  # should be 0 for the reference image
```

### Step 7: Validate with LLM (Optional)

```bash
uv run gux-tool verify ./tmp reference.png --gux page.gux --provider groq
```

The LLM verifier reads the JSON extraction report and the `.gux` spec text. It should report PASS for all zones on a known-good reference.

## Common Calibration Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `distance: 3.2` on a "white" zone | Anti-aliased borders bleeding into the crop | Tighten bounds inward by 1-2px |
| `v_avg_transitions: 0.3` on a chart zone | Bounds miss the chart, crop only white space | Adjust bounds to include the chart area |
| Census shows 15% "other" | Gradients or images outside the Tailwind palette | Expected; note in doc comment |
| LLM says FAIL but extraction looks correct | Ambiguous spec language | Improve `///` doc comments to clarify intent |

## Output: Calibrated Spec

A calibrated `.gux` spec should:
- Pass `gux-tool all ... --fail-on-delta=20` on the reference image with exit code 0.
- Pass all `Assert()` checks on the reference image.
- Have colour deltas < 5.0 for all zones.
- Have Assert thresholds set at ~40-50% of measured reference values.
