"""Crop zones by Bounds from the .gux spec and save as PNGs.

Parses the .gux file for all Zone declarations with Bounds(...).
Crops each region from the screenshot using PIL and saves to
<tmp_dir>/<zone_name>.png.

Requires --gux to be useful. Without it, saves the full image as one zone.

Example:
    uv run gux-tool zones ./tmp screenshot.png --gux dashboard.gux
"""

import os

from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='zones',
    help='Crop zones by Bounds(...) from the .gux spec. Save each as a separate PNG.',
)


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    os.makedirs(args.tmp_dir, exist_ok=True)
    for zone in zones:
        path = os.path.join(args.tmp_dir, f'{zone.name}.png')
        zone.image.save(path)
        report.add(
            zone.name,
            'zones',
            {
                'file': path,
                'width': zone.image.width,
                'height': zone.image.height,
            },
        )
