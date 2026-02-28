# Writing a GUX Spec from Scratch

## When to Use

When the user has a UI design (Figma, mockup, verbal description, wireframe) and needs a `.gux` spec file written for it. There is no existing screenshot to reverse-engineer from.

## Workflow

1. Clarify the page name, viewport dimensions, and overall theme (light/dark, background colour).
2. Identify the major zones: header, sidebar, main content, footer, modals. Each zone gets a name, bounds, and style.
3. For each zone, determine:
   - Pixel bounds `Bounds(x1, y1, x2, y2)` relative to the viewport
   - Expected background colour (hex or Tailwind shorthand)
   - Border/divider styles if visually significant
   - Child widgets (fictional names are fine)
   - `Assert()` thresholds for zones that must contain visual content (charts, tables)
4. Write `///` doc comments for intent, constraints, and warnings.
5. Use `Dynamic('name')` for runtime-variable content.

## File Structure

```dart
// IMPORTANT: GUX is pseudo-code; imports are intent markers.
import 'gux:core';        // Page, Zone, Style, Bounds
import 'gux:tw';          // Tailwind shorthand (tw.white, tw.slate50, etc.)
import 'gux:controls';    // Dropdown, Checkbox, Tile, Table, etc.
import 'gux:charts';      // Chart widgets

/// Page-level doc comment describing the page's purpose.
Page('page-name',
  viewport: Viewport(WIDTH, HEIGHT),
  style: Style(bg: '#hex', text: '#hex', theme: 'light'),

  Zone('zone-name',
    bounds: Bounds(x1, y1, x2, y2),
    style: Style(bg: '#hex'),
    children: [ ... ],
  ),
)
```

## Bounds Calculation

- Bounds are `(x1, y1, x2, y2)` — top-left to bottom-right in pixels.
- `x1, y1` is the top-left corner of the zone.
- `x2, y2` is the bottom-right corner.
- Zones must not exceed the viewport dimensions.
- Adjacent zones should share edges exactly (no gaps, no overlaps).
- A full-width bar at the top of a 1280x800 viewport: `Bounds(0, 0, 1280, 60)`.

## Style Properties

| Property | Example | Notes |
|----------|---------|-------|
| `bg` | `'#f8fafc'` or `tw.slate50` | Background colour |
| `text` | `'#0f172a'` | Text colour |
| `font` | `'bold'` or `'600'` | Font weight |
| `size` | `'3xl'` or `'14px'` | Text size |
| `colour` | `'#2563eb'` | Foreground/accent |
| `border` | `'1px solid #e2e8f0'` | Border shorthand |
| `rounded` | `'xl'` | Border radius |
| `p` | `4` | Padding (Tailwind units) |
| `theme` | `'light'` or `'dark'` | Theme hint |

## Assert Properties

Use `Assert()` for zones that must contain visual content:

```dart
Zone('chart-area',
  bounds: Bounds(0, 148, 480, 580),
  style: Style(bg: tw.white),
  assert: Assert(min_transitions_v: 10, min_transitions_h: 5),
)
```

| Property | Type | Meaning |
|----------|------|---------|
| `min_transitions_v` | int | Min avg vertical colour transitions per sampled line |
| `min_transitions_h` | int | Min avg horizontal colour transitions per sampled line |
| `min_regions` | int | Min detected sub-regions (tiles, cards, cells) |
| `non_blank` | bool | Shorthand for "any visual content present" |

## Tailwind Shorthand

Use `tw.` prefix for Tailwind colours:

```
tw.white       #ffffff     tw.slate50    #f8fafc
tw.black       #000000     tw.slate100   #f1f5f9
tw.slate200    #e2e8f0     tw.slate300   #cbd5e1
tw.slate500    #64748b     tw.slate800   #1e293b
tw.slate900    #0f172a     tw.blue600    #2563eb
tw.teal600     #0d9488     tw.red600     #dc2626
tw.amber600    #d97706     tw.green600   #16a34a
```

Full Tailwind palette is available.

## Fictional Widgets

Any widget name is valid. Use names that describe the component:

```dart
MyCustomChart(xAxis: 'date', yAxis: 'value', colours: ['#2563eb'])
KPITile(label: 'Revenue', value: Dynamic('revenue'))
StatusBadge(status: Dynamic('status'), style: Style(rounded: 'full'))
```

## Common Patterns

### Dashboard with KPI tiles + charts + table
```dart
Zone('kpi-row',     bounds: Bounds(0, 48, 960, 148), ...)
Zone('chart-left',  bounds: Bounds(0, 148, 480, 580), ...)
Zone('chart-right', bounds: Bounds(480, 148, 960, 580), ...)
Zone('table',       bounds: Bounds(0, 580, 960, 900), ...)
```

### Sidebar + main panel
```dart
Zone('sidebar', bounds: Bounds(0, 0, 280, 800), ...)
Zone('main',    bounds: Bounds(280, 0, 1280, 800), ...)
```

### Header + content + footer
```dart
Zone('header',  bounds: Bounds(0, 0, 1280, 60), ...)
Zone('content', bounds: Bounds(0, 60, 1280, 740), ...)
Zone('footer',  bounds: Bounds(0, 740, 1280, 800), ...)
```

## Checklist

- [ ] One `Page()` per file
- [ ] `viewport:` matches the target screenshot dimensions
- [ ] Every zone with visual assertions has `bounds:`
- [ ] `bg:` colours are hex or `tw.` shorthand
- [ ] Chart/table zones have `Assert()` thresholds
- [ ] `///` doc comments explain constraints and intent
- [ ] `Dynamic('name')` for all runtime-variable values
- [ ] File extension is `.gux`
