"""Compare named colour shifts between reference and current screenshot.

Requires --ref reference image. For each zone, runs census on both the
reference crop and the current crop, then computes the shift in named
Tailwind colour percentages.

Catches structural absence without k-means:
  Ref:     black:40%, blue500:25%, teal600:18%  → chart present
  Current: slate100:78%, white:15%              → chart gone blank

Output per zone:
  - top colours in ref vs current
  - shifts: colours that gained or lost >5% share
  - flag if the dominant named colour changed entirely

Example:
    uv run gux-tool census-diff ./tmp current.png --gux page.gux --ref ref.png
"""

import numpy as np
from PIL import Image

from gux_checker.core.palette import nearest_colour
from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='census-diff',
    help='Compare named colour shifts between reference and current. Requires --ref.',
)

SAMPLE_SIZE = 10000
SHIFT_THRESHOLD = 5.0  # percentage points — shifts below this are noise


def _census(image: Image.Image) -> dict[str, float]:
    """Sample image pixels, map to nearest Tailwind colour, return percentage dict."""
    arr = np.array(image.convert('RGB'))
    pixels = arr.reshape(-1, 3)
    n = min(SAMPLE_SIZE, len(pixels))
    if len(pixels) > n:
        indices = np.random.default_rng(42).choice(len(pixels), n, replace=False)
        pixels = pixels[indices]

    counts: dict[str, int] = {}
    for px in pixels:
        name, _ = nearest_colour((int(px[0]), int(px[1]), int(px[2])), threshold=50)
        key = name if name else '(other)'
        counts[key] = counts.get(key, 0) + 1

    total = sum(counts.values())
    return {k: round(v / total * 100, 1) for k, v in sorted(counts.items(), key=lambda x: -x[1])}


def _compute_shifts(ref: dict[str, float], cur: dict[str, float]) -> list[dict]:
    """Find colours that shifted by more than SHIFT_THRESHOLD percentage points."""
    all_colours = set(ref) | set(cur)
    shifts = []
    for colour in all_colours:
        ref_pct = ref.get(colour, 0.0)
        cur_pct = cur.get(colour, 0.0)
        delta = cur_pct - ref_pct
        if abs(delta) >= SHIFT_THRESHOLD:
            shifts.append(
                {
                    'colour': colour,
                    'ref_pct': ref_pct,
                    'cur_pct': cur_pct,
                    'delta': round(delta, 1),
                }
            )
    shifts.sort(key=lambda x: -abs(x['delta']))
    return shifts


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    if not hasattr(args, 'ref') or not args.ref:
        for zone in zones:
            report.add(zone.name, 'census-diff', {'error': '--ref reference image required'})
        return

    ref_img = Image.open(args.ref).convert('RGB')

    for zone in zones:
        x1, y1, x2, y2 = zone.bounds
        ref_crop = ref_img.crop((x1, y1, x2, y2))

        ref_census = _census(ref_crop)
        cur_census = _census(zone.image)

        shifts = _compute_shifts(ref_census, cur_census)

        # Flag if dominant colour changed
        ref_top = next(iter(ref_census), None)
        cur_top = next(iter(cur_census), None)
        dominant_changed = ref_top != cur_top

        report.add(
            zone.name,
            'census-diff',
            {
                'ref_top': list(ref_census.items())[:5],
                'cur_top': list(cur_census.items())[:5],
                'shifts': shifts,
                'dominant_changed': dominant_changed,
            },
        )

        if dominant_changed:
            report.record_fail(zone.name)
        else:
            report.record_pass(zone.name)
