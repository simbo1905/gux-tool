# Reverse-Engineering a GUX Spec from an Existing UI

## When to Use

When the user has an existing screenshot, HTML page, Figma export, or PDF mockup and wants to generate a `.gux` spec that describes it. The goal is to create a spec that `gux-tool` can then use for ongoing visual regression testing.

## Workflow

### From a Screenshot

1. Run `gux-tool` extraction to gather raw data:
   ```bash
   uv run gux-tool all ./tmp screenshot.png --json
   ```
2. Examine the JSON report. The full-image extraction gives dominant colours, transitions, and regions.
3. Use the extracted data to identify zone boundaries:
   - Horizontal colour transitions indicate vertical dividers (sidebar edges, panel borders).
   - Vertical colour transitions indicate horizontal dividers (headers, footers, section breaks).
   - Sub-region detection reveals tiles, cards, and grid cells.
4. Draft the `.gux` spec with zones matching the detected regions.
5. Calibrate bounds against the actual pixel coordinates from the report.

### From HTML / a Live Page

1. Take a screenshot at the target viewport size (e.g., 1280x800).
   - Headless Chrome: `chrome --headless --screenshot --window-size=1280,800 http://localhost:3000`
   - Playwright: `page.screenshot({ path: 'screenshot.png', fullPage: false })`
2. Use browser DevTools to read element positions and dimensions.
3. Map each major element to a `Zone()` with `Bounds()` matching its bounding box.
4. Extract computed background colours from DevTools and write `Style(bg: '#hex')`.
5. For charts/graphs/tables, add `Assert()` with appropriate thresholds.

### From a PDF / Static Mockup

1. Rasterise at a known DPI. The viewport in the `.gux` must match the rasterised pixel dimensions.
2. Identify zones by visual inspection. Measure pixel coordinates using an image editor or the `regions` technique.
3. Write the spec, using `Dynamic('name')` for any content that varies between renders.

### From a Figma Export

1. Use Figma's "Copy as SVG" or export frames as PNG at 1x scale.
2. Frame dimensions in Figma map directly to `Viewport(w, h)`.
3. Layer/frame positions map to `Bounds(x, y, x+w, y+h)`.
4. Fill colours from Figma map to `Style(bg: '#hex')`.

## Iterative Refinement

After writing the initial spec:

1. Run extraction against the screenshot with the spec:
   ```bash
   uv run gux-tool all ./tmp screenshot.png --gux page.gux --json
   ```
2. Check each zone's colour distance. If `distance > 5`, adjust the expected `bg` colour.
3. Check Assert results. If a chart zone shows 0 transitions, verify the bounds actually crop the chart area.
4. Tighten bounds if zones include padding or borders from adjacent zones.

## Tips

- Start coarse (3-5 large zones), then subdivide as needed.
- Name zones semantically: `header`, `sidebar`, `chart-left`, not `zone1`, `zone2`.
- Use `///` doc comments liberally. They help the LLM verifier understand intent.
- If the background is a gradient or image, use the dominant colour and note the pattern in a doc comment.
- For responsive layouts, create separate `.gux` files per breakpoint (desktop, tablet, mobile) with different viewports and bounds.
