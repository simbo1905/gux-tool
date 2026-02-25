"""Shared types for gux-tool: Technique, ZoneImage, Report, GuxZone, GuxSpec."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from PIL import Image


@dataclass
class GuxAssert:
    """Structural presence assertions for a zone, from Assert(...) in .gux spec."""

    min_transitions_v: float | None = None  # min avg vertical colour transitions per line
    min_transitions_h: float | None = None  # min avg horizontal colour transitions per line
    min_regions: int | None = None  # min number of detected sub-regions
    non_blank: bool = False  # shorthand: any visual content present


@dataclass
class GuxZone:
    """A zone parsed from a .gux spec file."""

    name: str
    bounds: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    expected_bg: str | None = None  # resolved hex colour
    doc: str | None = None  # /// doc comments
    assertions: GuxAssert | None = None  # Assert(...) structural checks


@dataclass
class GuxSpec:
    """Parsed .gux file."""

    page_name: str
    viewport: tuple[int, int]  # (width, height)
    zones: list[GuxZone] = field(default_factory=list)
    raw: str = ''  # original file text


@dataclass
class ZoneImage:
    """A cropped zone image ready for analysis."""

    name: str
    bounds: tuple[int, int, int, int]
    image: Image.Image
    expected_bg: str | None = None
    doc: str | None = None
    assertions: GuxAssert | None = None


class Technique:
    """A self-registering analysis technique.

    Usage in a technique module:

        technique = Technique(name='colours', help='Extract dominant colours')

        @technique.run
        def run(zones, report, args):
            ...
    """

    def __init__(self, name: str, help: str = ''):
        self.name = name
        self.help = help
        self._run_fn: Callable | None = None

    def run(self, fn: Callable) -> Callable:
        """Decorator to register the run function."""
        self._run_fn = fn
        return fn

    def execute(self, zones: list[ZoneImage], report: Report, args: Any) -> None:
        """Execute the technique's run function."""
        if self._run_fn is None:
            raise RuntimeError(f'Technique {self.name} has no run function')
        self._run_fn(zones, report, args)


@dataclass
class Report:
    """Accumulates results from techniques for text/JSON output."""

    image_path: str = ''
    image_width: int = 0
    image_height: int = 0
    gux_path: str | None = None
    zones: dict[str, dict[str, Any]] = field(default_factory=dict)
    pass_count: int = 0
    fail_count: int = 0

    def add(self, zone_name: str, technique_name: str, data: dict[str, Any]) -> None:
        """Add technique results for a zone."""
        if zone_name not in self.zones:
            self.zones[zone_name] = {'bounds': None, 'techniques': {}}
        self.zones[zone_name]['techniques'][technique_name] = data

    def set_bounds(self, zone_name: str, bounds: tuple[int, int, int, int]) -> None:
        """Set the bounds for a zone in the report."""
        if zone_name not in self.zones:
            self.zones[zone_name] = {'bounds': None, 'techniques': {}}
        self.zones[zone_name]['bounds'] = list(bounds)

    def record_pass(self, zone_name: str) -> None:
        self.pass_count += 1

    def record_fail(self, zone_name: str) -> None:
        self.fail_count += 1
