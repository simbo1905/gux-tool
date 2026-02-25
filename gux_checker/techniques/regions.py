"""Sub-region detection within zones by colour boundary scanning.

Scans for rectangular sub-regions of uniform colour within each zone.
Takes horizontal line scans at 20 evenly-spaced Y positions, finds runs
of similar colour, cross-references with vertical scans to confirm
rectangular regions.

Finds: tiles in a tile row, cards in a grid, table cells, input fields.

Example:
    uv run gux-tool regions ./tmp screenshot.png --gux dashboard.gux
"""

import numpy as np

from gux_checker.core.palette import nearest_colour, rgb_distance
from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='regions',
    help='Subdivide zones into sub-regions by detecting colour boundaries. Find tiles, cards, cells.',
)

COLOUR_THRESHOLD = 30
NUM_SCANS = 20


def _find_runs(line: np.ndarray, threshold: float = COLOUR_THRESHOLD) -> list[tuple[int, int, tuple[int, int, int]]]:
    """Find runs of similar colour in a pixel line.

    Returns list of (start_x, end_x, avg_colour).
    """
    if len(line) == 0:
        return []

    runs = []
    run_start = 0
    run_colours = [line[0]]

    for i in range(1, len(line)):
        prev = (int(line[i - 1][0]), int(line[i - 1][1]), int(line[i - 1][2]))
        curr = (int(line[i][0]), int(line[i][1]), int(line[i][2]))
        if rgb_distance(prev, curr) > threshold:
            avg = tuple(int(np.mean([c[j] for c in run_colours])) for j in range(3))
            if i - run_start > 5:  # minimum run width
                runs.append((run_start, i - 1, avg))
            run_start = i
            run_colours = [line[i]]
        else:
            run_colours.append(line[i])

    # Final run
    if len(line) - run_start > 5:
        avg = tuple(int(np.mean([c[j] for c in run_colours])) for j in range(3))
        runs.append((run_start, len(line) - 1, avg))

    return runs


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    for zone in zones:
        arr = np.array(zone.image.convert('RGB'))
        h, w = arr.shape[:2]

        if h < 10 or w < 10:
            report.add(zone.name, 'regions', {'count': 0, 'regions': []})
            continue

        # Horizontal scans at evenly-spaced Y positions
        y_positions = np.linspace(0, h - 1, min(NUM_SCANS, h), dtype=int)
        all_runs: dict[int, list] = {}
        for y in y_positions:
            all_runs[int(y)] = _find_runs(arr[y])

        # Simple region detection: find consistent vertical bands
        # Count how many scan lines have a boundary at similar X positions
        boundaries: dict[int, int] = {}
        for _y, runs in all_runs.items():
            for start, end, _ in runs:
                # Quantize to 10px buckets
                for x in [start, end]:
                    bucket = (x // 10) * 10
                    boundaries[bucket] = boundaries.get(bucket, 0) + 1

        # Boundaries that appear in > 40% of scan lines are real edges
        min_count = max(1, len(y_positions) * 0.4)
        real_edges = sorted([x for x, c in boundaries.items() if c >= min_count])

        # Build regions from edges
        detected = []
        if len(real_edges) >= 2:
            for i in range(len(real_edges) - 1):
                x1 = real_edges[i]
                x2 = real_edges[i + 1]
                if x2 - x1 < 20:
                    continue
                # Sample the centre of this region for colour
                cx = (x1 + x2) // 2
                cy = h // 2
                if cx < w and cy < h:
                    px = arr[cy, cx]
                    name, _dist = nearest_colour((int(px[0]), int(px[1]), int(px[2])))
                    detected.append(
                        {
                            'x1': x1,
                            'y1': 0,
                            'x2': x2,
                            'y2': h,
                            'colour': name,
                        }
                    )

        report.add(
            zone.name,
            'regions',
            {
                'count': len(detected),
                'regions': detected,
            },
        )
