"""Pixel diff between reference and current screenshot.

Requires --ref reference image. Resizes current to match reference if
dimensions differ. Per-zone pixel diff: computes percentage of pixels
that differ by more than RGB distance 20.

Generates a diff image per zone: green = match, red = mismatch.
Saves to <tmp_dir>/<zone_name>_diff.png.

Example:
    uv run gux-tool compare ./tmp current.png --gux page.gux --ref reference.png
"""

import os

import numpy as np
from PIL import Image

from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='compare',
    help='Pixel-diff two images (reference vs current). Output mismatch percentage per zone.',
)

DIFF_THRESHOLD = 20


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    if not hasattr(args, 'ref') or not args.ref:
        for zone in zones:
            report.add(zone.name, 'compare', {'error': '--ref reference image required'})
        return

    ref_img = Image.open(args.ref).convert('RGB')

    os.makedirs(args.tmp_dir, exist_ok=True)

    total_match = 0
    total_pixels = 0

    for zone in zones:
        x1, y1, x2, y2 = zone.bounds
        # Crop same bounds from reference
        ref_crop = ref_img.crop((x1, y1, x2, y2))
        cur_crop = zone.image

        # Resize if dimensions differ
        if ref_crop.size != cur_crop.size:
            ref_crop = ref_crop.resize(cur_crop.size, Image.Resampling.LANCZOS)

        # Vectorized Euclidean distance calculation
        ref_arr = np.array(ref_crop).astype(int)
        cur_arr = np.array(cur_crop).astype(int)
        diffs = np.linalg.norm(ref_arr - cur_arr, axis=-1)
        matches = diffs <= DIFF_THRESHOLD

        h, w = ref_arr.shape[:2]
        match_count = int(np.sum(matches))
        pixel_count = h * w

        # Build diff image vectorized
        diff_img = np.zeros((h, w, 3), dtype=np.uint8)
        diff_img[matches] = [0, 200, 0]  # green = match
        diff_img[~matches] = [200, 0, 0]  # red = mismatch

        mismatch_pct = round((1.0 - match_count / max(pixel_count, 1)) * 100, 1)
        total_match += match_count
        total_pixels += pixel_count

        # Save diff image
        diff_path = os.path.join(args.tmp_dir, f'{zone.name}_diff.png')
        Image.fromarray(diff_img).save(diff_path)

        report.add(
            zone.name,
            'compare',
            {
                'mismatch_pct': mismatch_pct,
                'diff_image': diff_path,
            },
        )

    if total_pixels > 0:
        overall = round((1.0 - total_match / total_pixels) * 100, 1)
        report.add('_overall', 'compare', {'mismatch_pct': overall})
