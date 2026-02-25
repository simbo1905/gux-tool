# GUX: GUI UX Description Language

**RFC Draft 0.2** · February 2026

## Status

Draft. Public comment invited.

## Abstract

GUX is a non-compilable UI description language that follows Flutter/Dart widget tree syntax. It exists for one purpose: to give humans and LLMs a shared, readable contract for what a screen should look like — its layout, its zones, its colours, its component types — without any rendering engine, build toolchain, or runtime.

GUX files are consumed by AI models to verify screenshots. They are authored by humans (or models) from reference images, transcripts, and intent. They are never compiled, transpiled, or executed.

## Motivation

Modern agentic coding tools can read DOM, inspect CSS classes, and confirm that `bg-white` is present in the markup. What they cannot do is confirm that the rendered pixel at coordinates (400, 200) is actually white. The DOM is a description of intent. The screen is reality. When a stylesheet fails to load, a class is overridden by specificity, or a build hash goes stale, the DOM says one thing and the pixels say another.

There is no standard way to express "what this screen should look like" in a format that:

1. An LLM can read and reason about fluently
2. A simple image-processing script can verify against a screenshot
3. A human can read and understand in thirty seconds
4. Does not require a rendering engine, package manager, or compilation step

GUX fills this gap. It is deliberately a baby dialect of Dart — familiar enough that any model trained on Flutter can parse it instantly, stripped enough that there is no ambiguity about its purpose.

## Design Principles

1. **Follows Flutter, consciously.** Widget tree nesting, named parameters, constructor syntax. If you know Dart, you can read GUX. If you don't know Dart, you can still read GUX.

2. **Never compiles.** There is no `main()`, no `runApp()`, no `BuildContext`. GUX is a specification, not a program.

3. **Fictional widgets are first-class.** If your screen has a custom chart, you write `MyCustomChart(...)`. There is no widget registry. Anything you name becomes real within the spec.

4. **Inline documentation is encouraged.** Use `///` doc comments freely. They are part of the contract.

5. **Colour and style are explicit.** Every zone that has a visual contract declares its expected colours, borders, and typography. Tailwind utility names are accepted as shorthand alongside hex values.

6. **Bounding boxes are optional but powerful.** When verifying against a screenshot, pixel bounds turn a fuzzy description into a testable assertion.

## Syntax

### Imports (fictional)

Imports declare intent and group related widgets. They do not resolve to real packages.

```dart
import 'gux:core';             // Page, Zone, Style, Bounds
import 'gux:charts/echarts';   // EChartsBumpChart, EChartsBarChart, etc.
import 'gux:tw';               // Tailwind shorthand: tw.slate50, tw.white, etc.
import 'gux:controls';         // Dropdown, Checkbox, Tile, Card, Table
```

### Page Declaration

Every GUX file describes exactly one page.

```dart
/// My App — main dashboard view.
Page('dashboard',
  viewport: Viewport(1280, 800),
  style: Style(bg: '#f8fafc', text: '#0f172a', theme: 'light'),
```

### Zones

Zones are named rectangular regions of the screen. They nest like Flutter widgets.

```dart
  Zone('sidebar',
    bounds: Bounds(0, 0, 280, 800),
    style: Style(bg: '#ffffff', borderRight: '1px solid #e2e8f0'),
    children: [ ... ],
  ),
```

### Fictional Widgets

Any widget name is valid. The name IS the spec.

```dart
  MyCustomChart(
    xAxis: 'date',
    yAxis: 'value',
    colours: ['#2563eb', '#0d9488'],
  ),
```

### Style Properties

Style accepts any combination of these. Tailwind shorthand and hex are interchangeable.

```dart
Style(
  bg: '#f8fafc',          // or tw.slate50
  text: '#0f172a',        // text colour
  font: 'bold',           // weight
  size: '3xl',            // Tailwind text size or px value
  colour: '#2563eb',      // foreground / accent
  border: 'rounded-xl',   // border style shorthand
  ring: '1 black/10',     // ring shorthand
  p: 4,                   // padding (Tailwind units)
  overflow: 'scroll-x',   // overflow behaviour
  opacity: 0.5,           // opacity
  theme: 'light',         // light | dark
)
```

### Bounds

Pixel coordinates relative to the viewport. Used for screenshot zone extraction.

```dart
Bounds(x1, y1, x2, y2)   // top-left to bottom-right
Bounds(0, 0, 960, 130)    // full-width strip, 130px tall
```

When bounds are omitted, the zone is described structurally but cannot be pixel-verified.

### Dynamic Values

When a property varies at runtime, use `Dynamic('name')` to declare it. The verifier treats Dynamic as "present and non-empty" rather than checking a specific value.

```dart
colours: Dynamic('user-palette'),   // "there should be colours here"
series: Dynamic('data'),            // "there should be data here"
```

### Doc Comments

Triple-slash comments are part of the contract. They describe intent, constraints, and warnings.

```dart
/// FORBIDDEN: grey background regressions on this page.
/// Body MUST be #ffffff.
Page('detail',
  style: Style(bg: '#ffffff !important'),
```

## File Extension

`.gux` — one file per page.

## Verification

A GUX file is verified against a screenshot in two passes:

### Pass 1: Zone Extraction

For each zone with `bounds`, crop that region from the screenshot.

### Pass 2: Colour Assertion

For each cropped zone, extract dominant colours (k-means, histogram binning, or similar). Compare against the zone's declared `Style.bg`, `Style.text`, `Style.colour` values within a configurable tolerance (default: ΔE < 5 in CIELAB space).

### Pass 3 (optional): Structural Presence via Assert

For zones containing charts, tables, or specific widgets, declare structural expectations using `Assert(...)`. The verifier checks that the region meets these thresholds.

```dart
Zone('bump-chart',
  bounds: Bounds(0, 148, 480, 580),
  style: Style(bg: tw.white),
  assert: Assert(min_transitions_v: 10, min_transitions_h: 5),
)
```

#### Assert Properties

| Property | Type | Meaning |
|----------|------|---------|
| `min_transitions_v` | int | Minimum average vertical colour transitions per sampled line. A chart or image has many; a blank zone has ~0. |
| `min_transitions_h` | int | Minimum average horizontal colour transitions per sampled line. |
| `min_regions` | int | Minimum number of detected sub-regions (tiles, cards, cells). |
| `non_blank` | bool | Shorthand for "any visual content present" (equivalent to `min_transitions_v: 1`). |

Assert provides a **separate failure path** from colour Δ. Colour assertions (`Style.bg`) catch CSS regressions. Assert catches structural absence — "the chart zone is empty", "the table has no rows".

### Output

```
PASS  dashboard.gux
  ✓ sidebar          bg:#ffffff  got:#ffffff  ΔE=0.0
  ✓ header           bg:#1e293b  got:#1e293b  ΔE=0.0
  ✗ main-content     bg:#ffffff  got:#e2e8f0  ΔE=7.3  FAIL
  ✓ chart-zone       content:non-blank  OK

FAIL  1 zone colour mismatch
```

## Scope and Non-Goals

GUX does NOT:

- Compile or render anything
- Replace HTML, CSS, or any frontend framework
- Define behaviour, event handling, or state management
- Guarantee pixel-perfect reproduction
- Require any runtime, package manager, or toolchain

GUX DOES:

- Provide a human- and LLM-readable layout contract
- Enable pixel-level verification of screenshots via simple tooling
- Document the intended visual design in version control alongside the code
- Catch CSS regressions that DOM/class inspection misses
- Give agents something they can actually verify instead of reading class names and hoping

## Appendix A: Tailwind Shorthand (tw namespace)

```dart
tw.white      // #ffffff
tw.black      // #000000
tw.slate50    // #f8fafc
tw.slate100   // #f1f5f9
tw.slate300   // #cbd5e1
tw.slate500   // #64748b
tw.slate900   // #0f172a
tw.blue600    // #2563eb
tw.teal600    // #0d9488
tw.amber600   // #d97706
tw.red600     // #dc2626
// ... full Tailwind palette available
```

## Appendix B: Relationship to Flutter

| Concept | Flutter | GUX |
|---------|---------|-----|
| Widget tree | Compiled, rendered | Descriptive only |
| Imports | Real packages | Fictional namespaces |
| Custom widgets | Must extend Widget | Just name it |
| Style | Theme + individual properties | Style() with mixed Tailwind/hex |
| Layout | Constraints, flex, etc. | Bounds + structural nesting |
| State | StatefulWidget, Riverpod, etc. | Dynamic('name') placeholder |
| Execution | main() → runApp() | None. Never runs. |

## Appendix C: Full Example — Chat Interface

Everyone has seen a chat UI. This is a visual contract for one.

```
┌───────────────────────────────────────────────────────┐
│ SIDEBAR (280px)       │  MAIN                         │
│ ┌───────────────────┐ │  ┌─────────────────────────┐  │
│ │ 🔍 Search...      │ │  │ HEADER: Model · · ·     │  │
│ ├───────────────────┤ │  ├─────────────────────────┤  │
│ │ Today             │ │  │                         │  │
│ │  ○ Fix the login… │ │  │  USER BUBBLE    ┌────┐  │  │
│ │  ○ Draft email…   │ │  │  (right-align)  │blue│  │  │
│ │ Yesterday         │ │  │                 └────┘  │  │
│ │  ○ Compare libs…  │ │  │                         │  │
│ │  ○ Explain swap…  │ │  │  ┌────┐  ASST BUBBLE    │  │
│ └───────────────────┘ │  │  │whte│  (left-align)   │  │
│                       │  │  └────┘                  │  │
│ ┌───────────────────┐ │  ├─────────────────────────┤  │
│ │ 👤 User · Pro     │ │  │ [ Type a message…   ▶ ] │  │
│ └───────────────────┘ │  └─────────────────────────┘  │
└───────────────────────────────────────────────────────┘
```

```dart
import 'gux:core';
import 'gux:tw';
import 'gux:controls';

/// A standard AI chat interface. Sidebar with history,
/// main panel with message bubbles and input bar.
Page('chat',
  viewport: Viewport(1280, 800),
  style: Style(bg: tw.white, text: '#0f172a', theme: 'light'),

  /// ── SIDEBAR ───────────────────────────────────────────
  Zone('sidebar',
    bounds: Bounds(0, 0, 280, 800),
    style: Style(bg: '#f9fafb', borderRight: '1px solid #e5e7eb'),
    children: [

      SearchBox(placeholder: 'Search...',
        style: Style(m: 12, rounded: 'lg', bg: tw.white,
          border: '1px solid #d1d5db', px: 12, py: 8)),

      /// Conversations grouped by day.
      ConversationList(
        groups: Dynamic('date-groups'),
        child: ConversationItem(
          title: Label(Dynamic('title'),
            style: Style(text: 'sm', colour: '#111827',
              overflow: 'ellipsis', maxLines: 1)),
          style: Style(px: 12, py: 8,
            hover: Style(bg: '#f3f4f6'),
            active: Style(bg: '#e5e7eb')),
        ),
        groupHeader: Label(Dynamic('date-label'),
          style: Style(text: 'xs', font: '600', colour: '#6b7280',
            px: 12, py: 4)),
      ),

      /// User info pinned to bottom.
      Zone('user-info',
        style: Style(borderTop: '1px solid #e5e7eb', p: 12),
        children: [
          Row(gap: 8, children: [
            Avatar(size: 32, style: Style(rounded: 'full')),
            Column(children: [
              Label(Dynamic('user-name'), style: Style(text: 'sm', font: '500')),
              Label(Dynamic('plan'), style: Style(text: 'xs', colour: '#6b7280')),
            ]),
          ]),
        ],
      ),
    ],
  ),

  /// ── MAIN PANEL ────────────────────────────────────────
  Zone('main',
    bounds: Bounds(280, 0, 1280, 800),
    style: Style(bg: tw.white),
    children: [

      /// Header bar.
      Zone('header',
        bounds: Bounds(280, 0, 1280, 52),
        style: Style(borderBottom: '1px solid #e5e7eb', px: 20, py: 12),
        children: [
          Row(justify: 'space-between', children: [
            Label(Dynamic('model-name'),
              style: Style(text: 'sm', font: '600')),
            IconButton('more', icon: '···',
              style: Style(colour: '#6b7280')),
          ]),
        ],
      ),

      /// Messages — scrollable area, bubbles alternate sides.
      Zone('messages',
        bounds: Bounds(280, 52, 1280, 730),
        style: Style(overflow: 'scroll-y', px: 20, py: 16),
        children: [
          MessageList(
            items: Dynamic('messages'),
            child: MessageBubble(
              /// User: right-aligned, light blue.
              user: Style(bg: '#eff6ff', rounded: 'xl',
                px: 16, py: 10, maxWidth: '70%', align: 'right'),
              /// Assistant: left-aligned, white.
              assistant: Style(bg: tw.white, rounded: 'xl',
                px: 16, py: 10, maxWidth: '70%', align: 'left'),
            ),
          ),
        ],
      ),

      /// Input bar pinned to bottom.
      Zone('input-bar',
        bounds: Bounds(280, 730, 1280, 800),
        style: Style(borderTop: '1px solid #e5e7eb', px: 20, py: 12),
        children: [
          Row(gap: 8, children: [
            TextInput(placeholder: 'Type a message...',
              style: Style(flex: Flex(1), rounded: 'xl',
                border: '1px solid #d1d5db', px: 16, py: 10)),
            IconButton('send', icon: '▶',
              style: Style(bg: '#2563eb', text: tw.white,
                rounded: 'full', size: 40)),
          ]),
        ],
      ),
    ],
  ),
)
```

## License

CC-BY-4.0
