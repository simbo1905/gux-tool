"""Regex-based parser for .gux files.

Extracts Page name, viewport, and all Zones with bounds and expected styles.
Does NOT attempt to fully parse Dart syntax — regex is sufficient.
"""

import re

from gux_checker.core.palette import resolve_tw
from gux_checker.core.types import GuxAssert, GuxSpec, GuxZone


def parse_gux_file(path: str) -> GuxSpec:
    """Parse a .gux file from disk."""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    return parse_gux_string(text)


def parse_gux_string(text: str) -> GuxSpec:
    """Parse a .gux spec from a string."""
    page_name = _extract_page_name(text) or 'unknown'
    viewport = _extract_viewport(text) or (0, 0)
    zones = _extract_zones(text)
    return GuxSpec(
        page_name=page_name,
        viewport=viewport,
        zones=zones,
        raw=text,
    )


def _extract_page_name(text: str) -> str | None:
    m = re.search(r"Page\(\s*'([^']+)'", text)
    return m.group(1) if m else None


def _extract_viewport(text: str) -> tuple[int, int] | None:
    m = re.search(r'Viewport\(\s*(\d+)\s*,\s*(\d+)\s*\)', text)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return None


def _extract_zones(text: str) -> list[GuxZone]:
    """Find all Zone declarations that have Bounds."""
    zones = []
    # Find all Zone('name', ...) blocks
    # We need to find zones with bounds, and extract the Style(bg: ...) near them
    zone_pattern = re.compile(
        r"Zone\(\s*'([^']+)'\s*,",
        re.DOTALL,
    )
    for m in zone_pattern.finditer(text):
        zone_name = m.group(1)
        # Get the text from this Zone declaration to find its bounds and style
        # Look ahead from this match to find bounds and style within the same block
        start = m.start()
        block = _extract_block(text, start)
        bounds = _extract_bounds(block)
        if bounds is None:
            # Zone without bounds — skip (cannot be pixel-verified)
            continue
        expected_bg = _extract_bg(block)
        doc = _extract_doc_comment(text, start)
        assertions = _extract_assert(block)
        zones.append(
            GuxZone(
                name=zone_name,
                bounds=bounds,
                expected_bg=expected_bg,
                doc=doc,
                assertions=assertions,
            )
        )
    return zones


def _extract_block(text: str, start: int) -> str:
    """Extract the text block for a Zone starting at `start`.

    Walks forward counting parens to find the matching close.
    Returns up to 2000 chars as a safety limit.
    """
    depth = 0
    i = start
    end = min(len(text), start + 2000)
    while i < end:
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
        i += 1
    return text[start:end]


def _extract_bounds(block: str) -> tuple[int, int, int, int] | None:
    m = re.search(r'Bounds\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', block)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
    return None


def _extract_bg(block: str) -> str | None:
    """Extract bg colour from the first Style(bg: ...) in the block.

    Handles both hex (#ffffff) and tw.name shorthand.
    Only looks at the *first* Style in the block (the zone's own style).
    """
    # Match Style(... bg: '#hex' ...) or Style(... bg: "#hex" ...) or Style(... bg: tw.name ...)
    m = re.search(r"Style\([^)]*\bbg:\s*(?:['\"]([^'\"]+)['\"]|(tw\.\w+))", block)
    if m:
        if m.group(1):
            return m.group(1)
        elif m.group(2):
            return resolve_tw(m.group(2))
    return None


def _extract_assert(block: str) -> GuxAssert | None:
    """Extract Assert(...) structural assertions from a zone block.

    Handles: min_transitions_v, min_transitions_h, min_regions, non_blank.
    """
    m = re.search(r'assert\s*:\s*Assert\(([^)]+)\)', block)
    if not m:
        return None

    inner = m.group(1)
    result = GuxAssert()
    found_any = False

    # min_transitions_v: 10
    mv = re.search(r'min_transitions_v\s*:\s*(\d+(?:\.\d+)?)', inner)
    if mv:
        result.min_transitions_v = float(mv.group(1))
        found_any = True

    # min_transitions_h: 5
    mh = re.search(r'min_transitions_h\s*:\s*(\d+(?:\.\d+)?)', inner)
    if mh:
        result.min_transitions_h = float(mh.group(1))
        found_any = True

    # min_regions: 3
    mr = re.search(r'min_regions\s*:\s*(\d+)', inner)
    if mr:
        result.min_regions = int(mr.group(1))
        found_any = True

    # non_blank: true
    nb = re.search(r'non_blank\s*:\s*(true|false)', inner)
    if nb:
        result.non_blank = nb.group(1) == 'true'
        found_any = True

    return result if found_any else None


def _extract_doc_comment(text: str, zone_start: int) -> str | None:
    """Extract /// doc comments immediately preceding the Zone declaration."""
    # Walk backwards from zone_start to find consecutive /// lines
    lines_before = text[:zone_start].rstrip().split('\n')
    doc_lines = []
    for line in reversed(lines_before):
        stripped = line.strip()
        if stripped.startswith('///'):
            doc_lines.append(stripped[3:].strip())
        else:
            break
    if doc_lines:
        doc_lines.reverse()
        return '\n'.join(doc_lines)
    return None
