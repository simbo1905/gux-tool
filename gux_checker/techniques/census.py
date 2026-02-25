"""Map sampled pixels to nearest named Tailwind colour. Output percentages.

Samples up to 10,000 pixels per zone. Maps each pixel to the nearest
named Tailwind colour within threshold 50 (RGB Euclidean). Pixels beyond
threshold are counted as '(other)'.

Different from 'colours': colours finds dominant clusters via k-means,
census maps every sample to a known named colour.

Output: top 10 named colours with percentages per zone.

Example:
    uv run gux-tool census ./tmp screenshot.png --gux dashboard.gux
"""

import numpy as np

from gux_checker.core.palette import nearest_colour
from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='census',
    help='Map every sampled pixel to nearest named Tailwind colour. Output percentages per zone.',
)


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    for zone in zones:
        arr = np.array(zone.image.convert('RGB'))
        pixels = arr.reshape(-1, 3)

        n_samples = min(10000, len(pixels))
        if len(pixels) > n_samples:
            indices = np.random.default_rng(42).choice(len(pixels), n_samples, replace=False)
            pixels = pixels[indices]

        counts: dict[str, int] = {}
        for px in pixels:
            r, g, b = int(px[0]), int(px[1]), int(px[2])
            name, _dist = nearest_colour((r, g, b), threshold=50)
            key = name if name else '(other)'
            counts[key] = counts.get(key, 0) + 1

        total = sum(counts.values())
        top = sorted(counts.items(), key=lambda x: -x[1])[:10]
        result = [{'name': n, 'pct': round(c / total * 100, 1)} for n, c in top]

        report.add(zone.name, 'census', {'top': result, 'samples': total})
