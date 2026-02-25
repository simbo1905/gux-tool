"""Tests for Assert() parsing in gux_parser and assertion checking in lines."""

import numpy as np
from gux_checker.core.gux_parser import parse_gux_string
from gux_checker.core.types import Report, ZoneImage
from gux_checker.registry import discover
from PIL import Image


class TestAssertParsing:
    def test_min_transitions_v(self) -> None:
        gux = """
Page('test', viewport: Viewport(100, 100), style: Style(bg: '#fff'),
  Zone('chart',
    bounds: Bounds(0, 0, 100, 100),
    style: Style(bg: '#ffffff'),
    assert: Assert(min_transitions_v: 10),
  ),
)
"""
        result = parse_gux_string(gux)
        assert result.zones[0].assertions is not None
        assert result.zones[0].assertions.min_transitions_v == 10.0

    def test_min_transitions_h(self) -> None:
        gux = """
Page('test', viewport: Viewport(100, 100), style: Style(bg: '#fff'),
  Zone('table',
    bounds: Bounds(0, 0, 100, 100),
    style: Style(bg: '#ffffff'),
    assert: Assert(min_transitions_h: 5),
  ),
)
"""
        result = parse_gux_string(gux)
        assert result.zones[0].assertions is not None
        assert result.zones[0].assertions.min_transitions_h == 5.0

    def test_non_blank(self) -> None:
        gux = """
Page('test', viewport: Viewport(100, 100), style: Style(bg: '#fff'),
  Zone('content',
    bounds: Bounds(0, 0, 100, 100),
    style: Style(bg: '#ffffff'),
    assert: Assert(non_blank: true),
  ),
)
"""
        result = parse_gux_string(gux)
        assert result.zones[0].assertions is not None
        assert result.zones[0].assertions.non_blank is True

    def test_multiple_assertions(self) -> None:
        gux = """
Page('test', viewport: Viewport(100, 100), style: Style(bg: '#fff'),
  Zone('bump-chart',
    bounds: Bounds(0, 0, 100, 100),
    style: Style(bg: '#ffffff'),
    assert: Assert(min_transitions_v: 10, min_transitions_h: 5),
  ),
)
"""
        result = parse_gux_string(gux)
        a = result.zones[0].assertions
        assert a is not None
        assert a.min_transitions_v == 10.0
        assert a.min_transitions_h == 5.0

    def test_no_assert_returns_none(self) -> None:
        gux = """
Page('test', viewport: Viewport(100, 100), style: Style(bg: '#fff'),
  Zone('plain',
    bounds: Bounds(0, 0, 100, 100),
    style: Style(bg: '#ffffff'),
  ),
)
"""
        result = parse_gux_string(gux)
        assert result.zones[0].assertions is None

    def test_min_regions(self) -> None:
        gux = """
Page('test', viewport: Viewport(100, 100), style: Style(bg: '#fff'),
  Zone('tiles',
    bounds: Bounds(0, 0, 100, 100),
    style: Style(bg: '#ffffff'),
    assert: Assert(min_regions: 3),
  ),
)
"""
        result = parse_gux_string(gux)
        assert result.zones[0].assertions is not None
        assert result.zones[0].assertions.min_regions == 3


def _solid_image(r: int, g: int, b: int, w: int = 50, h: int = 50) -> Image.Image:
    arr = np.full((h, w, 3), [r, g, b], dtype=np.uint8)
    return Image.fromarray(arr)


def _striped_image(w: int = 50, h: int = 50) -> Image.Image:
    """Alternating black/white vertical stripes — high v-transitions."""
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for x in range(w):
        colour = 255 if x % 4 < 2 else 0
        arr[:, x, :] = colour
    return Image.fromarray(arr)


class TestLinesAssertions:
    def _run_lines(self, zone: ZoneImage) -> Report:
        report = Report()
        report.set_bounds(zone.name, zone.bounds)
        techniques = discover()
        techniques['lines'].execute([zone], report, object())
        return report

    def test_blank_zone_fails_non_blank(self) -> None:
        img = _solid_image(255, 255, 255)
        from gux_checker.core.types import GuxAssert

        zone = ZoneImage(
            name='chart',
            bounds=(0, 0, 50, 50),
            image=img,
            assertions=GuxAssert(non_blank=True),
        )
        report = self._run_lines(zone)
        assert report.fail_count > 0

    def test_striped_zone_passes_min_transitions_h(self) -> None:
        img = _striped_image()
        from gux_checker.core.types import GuxAssert

        zone = ZoneImage(
            name='chart',
            bounds=(0, 0, 50, 50),
            image=img,
            assertions=GuxAssert(min_transitions_h=5),
        )
        report = self._run_lines(zone)
        assert report.pass_count > 0
        assert report.fail_count == 0

    def test_assertion_result_in_report(self) -> None:
        img = _solid_image(200, 200, 200)
        from gux_checker.core.types import GuxAssert

        zone = ZoneImage(
            name='zone1',
            bounds=(0, 0, 50, 50),
            image=img,
            assertions=GuxAssert(min_transitions_v=20),
        )
        report = self._run_lines(zone)
        data = report.zones['zone1']['techniques']['lines']
        assert 'assertions' in data
        assert data['assertions'][0]['check'] == 'min_transitions_v'
        assert data['assertions'][0]['threshold'] == 20.0

    def test_no_assertions_no_pass_fail(self) -> None:
        img = _solid_image(255, 255, 255)
        zone = ZoneImage(name='plain', bounds=(0, 0, 50, 50), image=img)
        report = self._run_lines(zone)
        assert report.pass_count == 0
        assert report.fail_count == 0
