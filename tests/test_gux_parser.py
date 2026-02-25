"""Tests for gux_checker.gux_parser — regex-based .gux file parser."""

import os

from gux_checker.core.gux_parser import parse_gux_file, parse_gux_string

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
SAMPLE_GUX = os.path.join(FIXTURES_DIR, 'sample.gux')


class TestParseGuxFile:
    def test_loads_sample(self):
        result = parse_gux_file(SAMPLE_GUX)
        assert result is not None

    def test_page_name(self):
        result = parse_gux_file(SAMPLE_GUX)
        assert result.page_name == 'chat'

    def test_viewport(self):
        result = parse_gux_file(SAMPLE_GUX)
        assert result.viewport == (1280, 800)

    def test_finds_zones_with_bounds(self):
        result = parse_gux_file(SAMPLE_GUX)
        names = [z.name for z in result.zones]
        assert 'sidebar' in names
        assert 'main' in names
        assert 'header' in names
        assert 'messages' in names
        assert 'input-bar' in names

    def test_sidebar_bounds(self):
        result = parse_gux_file(SAMPLE_GUX)
        sidebar = next(z for z in result.zones if z.name == 'sidebar')
        assert sidebar.bounds == (0, 0, 280, 800)

    def test_main_bounds(self):
        result = parse_gux_file(SAMPLE_GUX)
        main = next(z for z in result.zones if z.name == 'main')
        assert main.bounds == (280, 0, 1280, 800)

    def test_header_bounds(self):
        result = parse_gux_file(SAMPLE_GUX)
        header = next(z for z in result.zones if z.name == 'header')
        assert header.bounds == (280, 0, 1280, 52)

    def test_sidebar_expected_bg(self):
        result = parse_gux_file(SAMPLE_GUX)
        sidebar = next(z for z in result.zones if z.name == 'sidebar')
        assert sidebar.expected_bg == '#f9fafb'

    def test_main_expected_bg_resolves_tw(self):
        result = parse_gux_file(SAMPLE_GUX)
        main = next(z for z in result.zones if z.name == 'main')
        # tw.white should resolve to #ffffff
        assert main.expected_bg == '#ffffff'

    def test_double_quotes_supported(self):
        gux = """
        Zone('test',
            bounds: Bounds(0, 0, 100, 100),
            style: Style(bg: "#ff0000"),
        )
        """
        result = parse_gux_string(gux)
        assert result.zones[0].expected_bg == '#ff0000'

    def test_zone_without_bounds_excluded(self):
        """user-info has no bounds — it should not appear in zones list."""
        result = parse_gux_file(SAMPLE_GUX)
        names = [z.name for z in result.zones]
        assert 'user-info' not in names

    def test_doc_comments_attached(self):
        result = parse_gux_file(SAMPLE_GUX)
        sidebar = next(z for z in result.zones if z.name == 'sidebar')
        assert sidebar.doc is not None
        assert 'SIDEBAR' in sidebar.doc


class TestParseGuxString:
    def test_minimal(self):
        gux = """
Page('test',
  viewport: Viewport(800, 600),
  style: Style(bg: '#ffffff'),
  Zone('header',
    bounds: Bounds(0, 0, 800, 50),
    style: Style(bg: '#1e293b'),
  ),
)
"""
        result = parse_gux_string(gux)
        assert result.page_name == 'test'
        assert result.viewport == (800, 600)
        assert len(result.zones) == 1
        assert result.zones[0].name == 'header'
        assert result.zones[0].bounds == (0, 0, 800, 50)
        assert result.zones[0].expected_bg == '#1e293b'

    def test_tw_shorthand(self):
        gux = """
Page('tw-test',
  viewport: Viewport(100, 100),
  style: Style(bg: tw.slate50),
  Zone('box',
    bounds: Bounds(0, 0, 100, 100),
    style: Style(bg: tw.blue600),
  ),
)
"""
        result = parse_gux_string(gux)
        assert result.zones[0].expected_bg == '#2563eb'

    def test_no_zones(self):
        gux = """
Page('empty',
  viewport: Viewport(100, 100),
  style: Style(bg: '#fff'),
)
"""
        result = parse_gux_string(gux)
        assert result.page_name == 'empty'
        assert len(result.zones) == 0
