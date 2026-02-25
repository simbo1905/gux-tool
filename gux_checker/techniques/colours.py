"""Dominant colour extraction per zone using k-means clustering.

Samples up to 5000 pixels per zone, runs KMeans (n_clusters=5, n_init=3).
For each cluster centre, finds the nearest named Tailwind colour within
threshold 30 (RGB Euclidean distance).

If a .gux spec provides expected_bg for a zone, compares the dominant
colour against it and reports pass/fail with distance.

Falls back to histogram quantization if sklearn is not available.

Example:
    uv run gux-tool colours ./tmp screenshot.png --gux dashboard.gux
"""

import numpy as np

from gux_checker.core.palette import hex_to_rgb, nearest_colour, rgb_distance
from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='colours',
    help='Dominant colour extraction per zone (k-means). Compare against expected bg.',
)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f'#{r:02x}{g:02x}{b:02x}'


def _extract_dominant(image, n_clusters: int = 5, n_samples: int = 5000) -> list[dict]:
    """Extract dominant colours using KMeans. Fallback to histogram if sklearn unavailable."""
    arr = np.array(image.convert('RGB'))
    pixels = arr.reshape(-1, 3)

    # Sample pixels
    if len(pixels) > n_samples:
        indices = np.random.default_rng(42).choice(len(pixels), n_samples, replace=False)
        pixels = pixels[indices]

    try:
        from sklearn.cluster import KMeans

        km = KMeans(n_clusters=min(n_clusters, len(pixels)), n_init=3, random_state=42)
        km.fit(pixels)
        centres = km.cluster_centers_.astype(int)
        labels = km.labels_
        counts = np.bincount(labels, minlength=len(centres))
        total = counts.sum()
    except ImportError:
        # Fallback: quantize to 32-level bins
        quantized = (pixels // 32) * 32 + 16
        unique, counts = np.unique(quantized, axis=0, return_counts=True)
        order = np.argsort(-counts)[:n_clusters]
        centres = unique[order]
        counts = counts[order]
        total = counts.sum()

    results = []
    for i, centre in enumerate(centres):
        r, g, b = int(centre[0]), int(centre[1]), int(centre[2])
        pct = float(counts[i]) / float(total) * 100.0
        name, _dist = nearest_colour((r, g, b), threshold=30)
        results.append(
            {
                'hex': _rgb_to_hex(r, g, b),
                'pct': round(pct, 1),
                'nearest': name,
                'r': r,
                'g': g,
                'b': b,
            }
        )

    # Sort by percentage descending
    results.sort(key=lambda x: -x['pct'])
    return results


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    for zone in zones:
        dominant = _extract_dominant(zone.image)
        data: dict = {'dominant': dominant}

        if zone.expected_bg:
            exp_rgb = hex_to_rgb(zone.expected_bg)
            # Dominant colour (highest %) is the "actual bg"
            if dominant:
                top = dominant[0]
                actual_rgb = (top['r'], top['g'], top['b'])
                dist = rgb_distance(exp_rgb, actual_rgb)
                passed = dist < 20  # ~ΔE 5
                data['expected_bg'] = zone.expected_bg
                data['actual_bg'] = top['hex']
                data['distance'] = round(dist, 1)
                data['pass'] = passed
                if passed:
                    report.record_pass(zone.name)
                else:
                    report.record_fail(zone.name)

        report.add(zone.name, 'colours', data)
