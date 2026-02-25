"""Integration test: screenshot test HTML with headless Chrome, then run gux-tool against it."""

import json
import subprocess
from pathlib import Path

import pytest
from gux_checker.core.gux_parser import parse_gux_file
from gux_checker.core.types import Report, ZoneImage
from gux_checker.registry import discover
from PIL import Image

TESTS_DIR = Path(__file__).parent
HTML_DIR = TESTS_DIR / 'html'
FIXTURES_DIR = TESTS_DIR / 'fixtures'
DASHBOARD_HTML = HTML_DIR / 'dashboard.html'
DASHBOARD_GUX = FIXTURES_DIR / 'dashboard.gux'

CHROME = 'google-chrome-stable'


def _chrome_available() -> bool:
    try:
        subprocess.run([CHROME, '--version'], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _screenshot(html_path: Path, output_path: Path, width: int = 960, height: int = 900) -> None:
    """Take a headless Chrome screenshot of an HTML file."""
    url = f'file://{html_path.resolve()}'
    subprocess.run(
        [
            CHROME,
            '--headless=new',
            '--no-sandbox',
            '--disable-gpu',
            '--disable-software-rasterizer',
            f'--window-size={width},{height}',
            f'--screenshot={output_path}',
            '--hide-scrollbars',
            url,
        ],
        capture_output=True,
        timeout=30,
        check=True,
    )


@pytest.fixture(scope='module')
def dashboard_screenshot(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Screenshot the dashboard HTML once for all tests in this module."""
    if not _chrome_available():
        pytest.skip('google-chrome-stable not available')
    tmp = tmp_path_factory.mktemp('screenshots')
    shot = tmp / 'dashboard.png'
    _screenshot(DASHBOARD_HTML, shot)
    assert shot.exists(), 'Screenshot was not created'
    return shot


class TestScreenshotCreated:
    def test_file_exists(self, dashboard_screenshot: Path) -> None:
        assert dashboard_screenshot.exists()

    def test_is_png(self, dashboard_screenshot: Path) -> None:
        img = Image.open(dashboard_screenshot)
        assert img.format == 'PNG'

    def test_dimensions(self, dashboard_screenshot: Path) -> None:
        img = Image.open(dashboard_screenshot)
        assert img.width == 960
        # Height may vary slightly with Chrome rendering
        assert img.height >= 800


class TestColoursAgainstGux:
    """Run the colours technique against the screenshot and check known zones."""

    def test_toolbar_bg_is_white(self, dashboard_screenshot: Path) -> None:
        img = Image.open(dashboard_screenshot).convert('RGB')
        spec = parse_gux_file(str(DASHBOARD_GUX))
        toolbar = next(z for z in spec.zones if z.name == 'toolbar')
        x1, y1, x2, y2 = toolbar.bounds
        crop = img.crop((x1, y1, x2, y2))

        zone = ZoneImage(
            name='toolbar',
            bounds=toolbar.bounds,
            image=crop,
            expected_bg=toolbar.expected_bg,
        )

        report = Report(image_path=str(dashboard_screenshot))
        techniques = discover()
        colours_tech = techniques['colours']

        # Create a minimal args object
        class Args:
            tmp_dir = str(dashboard_screenshot.parent)
            gux = str(DASHBOARD_GUX)
            json = False

        colours_tech.execute([zone], report, Args())
        data = report.zones['toolbar']['techniques']['colours']
        assert data['pass'] is True, (
            f'Toolbar bg mismatch: expected {data.get("expected_bg")}, '
            f'got {data.get("actual_bg")}, distance={data.get("distance")}'
        )

    def test_kpi_tiles_bg_is_white(self, dashboard_screenshot: Path) -> None:
        img = Image.open(dashboard_screenshot).convert('RGB')
        spec = parse_gux_file(str(DASHBOARD_GUX))
        kpi = next(z for z in spec.zones if z.name == 'kpi-tiles')
        x1, y1, x2, y2 = kpi.bounds
        crop = img.crop((x1, y1, x2, y2))

        zone = ZoneImage(name='kpi-tiles', bounds=kpi.bounds, image=crop, expected_bg=kpi.expected_bg)

        report = Report(image_path=str(dashboard_screenshot))
        techniques = discover()
        colours_tech = techniques['colours']

        class Args:
            tmp_dir = str(dashboard_screenshot.parent)
            gux = str(DASHBOARD_GUX)
            json = False

        colours_tech.execute([zone], report, Args())
        data = report.zones['kpi-tiles']['techniques']['colours']
        assert data['pass'] is True, (
            f'KPI bg mismatch: expected {data.get("expected_bg")}, '
            f'got {data.get("actual_bg")}, distance={data.get("distance")}'
        )


class TestAllTechniques:
    """Run 'all' and check we get a populated report."""

    def test_all_produces_report(self, dashboard_screenshot: Path) -> None:
        img = Image.open(dashboard_screenshot).convert('RGB')
        spec = parse_gux_file(str(DASHBOARD_GUX))

        zones = []
        for gz in spec.zones:
            x1, y1, x2, y2 = gz.bounds
            crop = img.crop((x1, y1, x2, y2))
            zones.append(
                ZoneImage(
                    name=gz.name,
                    bounds=gz.bounds,
                    image=crop,
                    expected_bg=gz.expected_bg,
                    doc=gz.doc,
                )
            )

        report = Report(
            image_path=str(dashboard_screenshot),
            image_width=img.width,
            image_height=img.height,
            gux_path=str(DASHBOARD_GUX),
        )
        for z in zones:
            report.set_bounds(z.name, z.bounds)

        class Args:
            tmp_dir = str(dashboard_screenshot.parent)
            gux = str(DASHBOARD_GUX)
            json = False
            ref = None

        techniques = discover()
        all_tech = techniques['all']
        all_tech.execute(zones, report, Args())

        # Should have results for every zone
        for gz in spec.zones:
            assert gz.name in report.zones, f'Missing zone: {gz.name}'
            techs = report.zones[gz.name]['techniques']
            assert 'colours' in techs, f'Missing colours for {gz.name}'
            assert 'lines' in techs, f'Missing lines for {gz.name}'
            assert 'census' in techs, f'Missing census for {gz.name}'

    def test_json_output(self, dashboard_screenshot: Path) -> None:
        """Check that JSON output is valid and has expected structure."""
        img = Image.open(dashboard_screenshot).convert('RGB')
        spec = parse_gux_file(str(DASHBOARD_GUX))

        zones = []
        for gz in spec.zones:
            x1, y1, x2, y2 = gz.bounds
            crop = img.crop((x1, y1, x2, y2))
            zones.append(
                ZoneImage(
                    name=gz.name,
                    bounds=gz.bounds,
                    image=crop,
                    expected_bg=gz.expected_bg,
                    doc=gz.doc,
                )
            )

        report = Report(
            image_path=str(dashboard_screenshot),
            image_width=img.width,
            image_height=img.height,
            gux_path=str(DASHBOARD_GUX),
        )
        for z in zones:
            report.set_bounds(z.name, z.bounds)

        class Args:
            tmp_dir = str(dashboard_screenshot.parent)
            gux = str(DASHBOARD_GUX)
            json = True
            ref = None

        techniques = discover()
        all_tech = techniques['all']
        all_tech.execute(zones, report, Args())

        from gux_checker.core.report import format_json

        output = format_json(report)
        parsed = json.loads(output)
        assert 'zones' in parsed
        assert 'summary' in parsed
        assert parsed['dimensions']['width'] == 960
