"""Report builder — text and JSON output for gux-tool results."""

import json
import os
from typing import Any

from gux_checker.core.types import Report


def format_text(report: Report, gux_path: str | None = None) -> str:
    """Format report as human-readable text."""
    lines = []
    dim = f'{report.image_width}\u00d7{report.image_height}'
    header = f'gux-tool: {report.image_path} ({dim})'
    if gux_path:
        zone_count = len(report.zones)
        header += f' \u2014 {os.path.basename(gux_path)} ({zone_count} zones)'
    lines.append(header)
    lines.append('')

    for zone_name, zone_data in report.zones.items():
        bounds = zone_data.get('bounds')
        if bounds:
            b = f'[{bounds[0]},{bounds[1]}\u2192{bounds[2]},{bounds[3]}]'
        else:
            b = ''
        lines.append(f'\u2500\u2500 {zone_name} {b}')

        techniques = zone_data.get('techniques', {})
        for tech_name, tech_data in techniques.items():
            if tech_name == 'colours' and 'expected_bg' in tech_data:
                exp = tech_data['expected_bg']
                got = tech_data.get('actual_bg', '?')
                dist = tech_data.get('distance', '?')
                passed = tech_data.get('pass', False)
                mark = '\u2713' if passed else '\u2717'
                lines.append(f'  bg: expected {exp}  got {got}  \u0394={dist}  {mark}')
            elif tech_name == 'ocr' and 'texts' in tech_data:
                lines.append(f'  text: {tech_data["texts"]}')
            elif tech_name == 'lines':
                h = tech_data.get('h_avg_transitions', '?')
                v = tech_data.get('v_avg_transitions', '?')
                lines.append(f'  transitions: h={h} v={v} avg/line')
            elif tech_name == 'census' and 'top' in tech_data:
                top3 = tech_data['top'][:3]
                parts = [f'{c["name"]}:{c["pct"]:.1f}%' for c in top3]
                lines.append(f'  census: {", ".join(parts)}')
            elif tech_name == 'regions' and 'count' in tech_data:
                lines.append(f'  sub-regions: {tech_data["count"]} detected')
            elif tech_name == 'compare' and 'mismatch_pct' in tech_data:
                pct = tech_data['mismatch_pct']
                lines.append(f'  diff: {pct:.1f}% mismatch')
            elif tech_name == 'zones':
                pass  # zone cropping doesn't add text output
            else:
                # Generic fallback
                for k, v in tech_data.items():
                    lines.append(f'  {tech_name}.{k}: {v}')

        lines.append('')

    total = report.pass_count + report.fail_count
    if total > 0:
        lines.append(f'PASS {report.pass_count}/{total} zones  FAIL {report.fail_count}/{total} zones')
    return '\n'.join(lines)


def format_json(report: Report) -> str:
    """Format report as JSON."""
    obj: dict[str, Any] = {
        'image': report.image_path,
        'dimensions': {'width': report.image_width, 'height': report.image_height},
    }
    if report.gux_path:
        obj['gux'] = report.gux_path

    obj['zones'] = []
    for zone_name, zone_data in report.zones.items():
        zone_obj = {
            'name': zone_name,
            'bounds': zone_data.get('bounds'),
            'techniques': zone_data.get('techniques', {}),
        }
        obj['zones'].append(zone_obj)

    obj['summary'] = {
        'total': report.pass_count + report.fail_count,
        'pass': report.pass_count,
        'fail': report.fail_count,
    }
    return json.dumps(obj, indent=2)
