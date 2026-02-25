"""Tests for gux_checker.palette — Tailwind colour map and distance functions."""

from gux_checker.core.palette import (
    TAILWIND,
    hex_to_rgb,
    nearest_colour,
    resolve_tw,
    rgb_distance,
)


class TestHexToRgb:
    def test_white(self):
        assert hex_to_rgb('#ffffff') == (255, 255, 255)

    def test_black(self):
        assert hex_to_rgb('#000000') == (0, 0, 0)

    def test_blue600(self):
        assert hex_to_rgb('#2563eb') == (37, 99, 235)

    def test_uppercase(self):
        assert hex_to_rgb('#FFFFFF') == (255, 255, 255)

    def test_short_hex(self):
        assert hex_to_rgb('#fff') == (255, 255, 255)

    def test_no_hash(self):
        assert hex_to_rgb('ff0000') == (255, 0, 0)

    def test_invalid_hex_returns_black(self):
        assert hex_to_rgb('invalid') == (0, 0, 0)
        assert hex_to_rgb('#ff') == (0, 0, 0)
        assert hex_to_rgb('#ffffffff') == (0, 0, 0)


class TestRgbDistance:
    def test_same_colour(self):
        assert rgb_distance((255, 255, 255), (255, 255, 255)) == 0.0

    def test_black_white(self):
        d = rgb_distance((0, 0, 0), (255, 255, 255))
        assert d > 400  # sqrt(3 * 255^2) ≈ 441.7

    def test_symmetry(self):
        a = (100, 50, 200)
        b = (120, 60, 180)
        assert rgb_distance(a, b) == rgb_distance(b, a)

    def test_uses_int_not_uint8(self):
        """Ensure no numpy uint8 overflow — (0 - 200) must not wrap."""
        d = rgb_distance((0, 0, 0), (200, 200, 200))
        assert d > 300


class TestNearestColour:
    def test_exact_white(self):
        name, dist = nearest_colour((255, 255, 255))
        assert name == 'white'
        assert dist == 0.0

    def test_exact_black(self):
        name, dist = nearest_colour((0, 0, 0))
        assert name == 'black'
        assert dist == 0.0

    def test_near_slate50(self):
        # #f8fafc = (248, 250, 252) — a pixel at (250, 251, 253) should match
        name, dist = nearest_colour((250, 251, 253))
        assert name == 'slate50'
        assert dist < 5

    def test_beyond_threshold_returns_none(self):
        # A colour far from any Tailwind colour
        name, _dist = nearest_colour((128, 1, 128), threshold=10)
        assert name is None


class TestResolveTw:
    def test_white(self):
        assert resolve_tw('tw.white') == '#ffffff'

    def test_slate50(self):
        assert resolve_tw('tw.slate50') == '#f8fafc'

    def test_blue600(self):
        assert resolve_tw('tw.blue600') == '#2563eb'

    def test_not_tw_passthrough(self):
        assert resolve_tw('#abcdef') == '#abcdef'

    def test_unknown_tw_returns_none(self):
        assert resolve_tw('tw.doesNotExist') is None


class TestTailwindPalette:
    def test_has_white(self):
        assert 'white' in TAILWIND

    def test_has_black(self):
        assert 'black' in TAILWIND

    def test_has_slate_range(self):
        for n in [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]:
            assert f'slate{n}' in TAILWIND

    def test_values_are_hex(self):
        for name, hex_val in TAILWIND.items():
            assert hex_val.startswith('#'), f'{name} value {hex_val} missing #'
            assert len(hex_val) == 7, f'{name} value {hex_val} not 7 chars'
