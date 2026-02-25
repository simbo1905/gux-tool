"""Horizontal/vertical line scanning for colour transitions.

Samples 10 horizontal and 10 vertical lines evenly spaced across each zone.
Walks each line pixel by pixel, records positions where RGB distance to
previous pixel exceeds 30.

Output: average transitions per line (horizontal and vertical).
  - High h-transitions + low v-transitions = horizontal bands (headers, rows)
  - Low h-transitions + high v-transitions = vertical panels (sidebars)

Also checks Assert() thresholds from the .gux spec if present:
  assert: Assert(min_transitions_v: 10, min_transitions_h: 5)
  assert: Assert(non_blank: true)

A zone that should contain a chart but is blank will have v~0. A zone
that should contain a table will have h > some threshold. These checks
record pass/fail on the report independently of colour Δ.

Example:
    uv run gux-tool lines ./tmp screenshot.png --gux dashboard.gux
"""

import numpy as np

from gux_checker.core.palette import rgb_distance
from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='lines',
    help='Colour transition scanning. Checks Assert() thresholds from .gux spec.',
)

TRANSITION_THRESHOLD = 30
NUM_LINES = 10


def _count_transitions(line: np.ndarray) -> int:
    """Count positions where RGB distance to previous pixel exceeds threshold."""
    count = 0
    for i in range(1, len(line)):
        a = (int(line[i - 1][0]), int(line[i - 1][1]), int(line[i - 1][2]))
        b = (int(line[i][0]), int(line[i][1]), int(line[i][2]))
        if rgb_distance(a, b) > TRANSITION_THRESHOLD:
            count += 1
    return count


def _check_assertions(
    zone: ZoneImage,
    h_avg: float,
    v_avg: float,
    report: Report,
) -> list[dict]:
    """Check Assert() thresholds. Returns list of assertion results."""
    a = zone.assertions
    if a is None:
        return []

    results = []

    if a.non_blank or a.min_transitions_v is not None:
        # non_blank is shorthand for min_transitions_v >= 1
        threshold_v = a.min_transitions_v if a.min_transitions_v is not None else 1.0
        passed = v_avg >= threshold_v
        results.append(
            {
                'check': 'min_transitions_v',
                'threshold': threshold_v,
                'got': v_avg,
                'pass': passed,
            }
        )
        if passed:
            report.record_pass(zone.name)
        else:
            report.record_fail(zone.name)

    if a.min_transitions_h is not None:
        passed = h_avg >= a.min_transitions_h
        results.append(
            {
                'check': 'min_transitions_h',
                'threshold': a.min_transitions_h,
                'got': h_avg,
                'pass': passed,
            }
        )
        if passed:
            report.record_pass(zone.name)
        else:
            report.record_fail(zone.name)

    return results


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    for zone in zones:
        arr = np.array(zone.image.convert('RGB'))
        h, w = arr.shape[:2]

        if h < 2 or w < 2:
            report.add(zone.name, 'lines', {'h_avg_transitions': 0, 'v_avg_transitions': 0})
            continue

        h_transitions = []
        y_positions = np.linspace(0, h - 1, min(NUM_LINES, h), dtype=int)
        for y in y_positions:
            h_transitions.append(_count_transitions(arr[y]))

        v_transitions = []
        x_positions = np.linspace(0, w - 1, min(NUM_LINES, w), dtype=int)
        for x in x_positions:
            v_transitions.append(_count_transitions(arr[:, x]))

        h_avg = round(sum(h_transitions) / max(len(h_transitions), 1), 1)
        v_avg = round(sum(v_transitions) / max(len(v_transitions), 1), 1)

        data: dict = {'h_avg_transitions': h_avg, 'v_avg_transitions': v_avg}

        assertion_results = _check_assertions(zone, h_avg, v_avg, report)
        if assertion_results:
            data['assertions'] = assertion_results

        report.add(zone.name, 'lines', data)
