"""gux-tool — Visual regression testing for UI screenshots using GUX specs.

Usage: uv run gux-tool <technique> <tmp_dir> <image> [options]

Techniques are auto-discovered from gux_checker/techniques/.
Each technique module's docstring is its documentation.
Run `gux-tool help <technique>` for full module docs.

Environment variables / .env loading:
  OS environment variables are always used first.
  If a variable is not set, gux-tool looks for a .env file starting from
  the current directory and walking up, stopping at the nearest .git boundary.
  Use --env-file to override the .env location explicitly.
"""

import argparse
import importlib
import os
import sys

from PIL import Image

from gux_checker import registry
from gux_checker.core.env import load_env
from gux_checker.core.gux_parser import parse_gux_file
from gux_checker.core.report import format_json, format_text
from gux_checker.core.types import Report, ZoneImage


def _load_technique_module(name: str) -> object:
    """Load the raw module for a technique (for docstring access)."""
    return importlib.import_module(f'gux_checker.techniques.{name}')


def _build_parser() -> argparse.ArgumentParser:
    techniques = registry.all_techniques()

    epilog = (
        'Examples:\n'
        '  gux-tool colours ./tmp screenshot.png --gux page.gux\n'
        '  gux-tool all ./tmp screenshot.png --gux page.gux --json\n'
        '  gux-tool all ./tmp screenshot.png --gux page.gux --fail-on-delta=20\n'
        '  gux-tool compare ./tmp current.png --gux page.gux --ref ref.png\n'
        '  gux-tool census-diff ./tmp current.png --gux page.gux --ref ref.png\n'
        '  gux-tool verify ./tmp screenshot.png --gux page.gux --provider mistral\n'
        '  gux-tool help colours\n'
        '  gux-tool rfc\n'
        '\n'
        'Provider env vars (set in .env or environment):\n'
        '  MISTRAL_API_KEY + MISTRAL_API_URL=https://api.mistral.ai/v1\n'
        '  GROQ_API_KEY    + GROQ_API_URL=https://api.groq.com/openai/v1\n'
        '  OPENAI_API_KEY  + OPENAI_API_URL=https://api.openai.com/v1\n'
        '  ANTHROPIC_API_KEY (native SDK, no URL needed)\n'
        '  Any OpenAI-compatible: NAME_API_KEY + NAME_API_URL\n'
    )
    parser = argparse.ArgumentParser(
        prog='gux-tool',
        description='Visual regression testing for UI screenshots using GUX specs.',
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    # Global --env-file option before subcommand
    parser.add_argument(
        '--env-file',
        metavar='PATH',
        default=None,
        help='Path to .env file (default: walk up from cwd to .git boundary)',
    )
    sub = parser.add_subparsers(dest='technique', help='Technique to run')

    # Auto-register each technique as a subcommand using module docstring
    for name, tech in sorted(techniques.items()):
        mod = _load_technique_module(name)
        short_help = (mod.__doc__ or '').strip().splitlines()[0] if (mod.__doc__ or '').strip() else tech.help

        p = sub.add_parser(name, help=short_help)
        p.add_argument('tmp_dir', help='Working directory for artefacts')
        p.add_argument('image', help='Path to screenshot PNG/JPG')
        p.add_argument('-g', '--gux', help='Path to .gux spec file')
        p.add_argument('-j', '--json', action='store_true', help='Output JSON instead of text')
        p.add_argument('-k', '--api-key', help='LLM API key (overrides env var)')
        p.add_argument(
            '-p',
            '--provider',
            default='anthropic',
            help='LLM provider name (default: anthropic). Any OpenAI-compatible name works.',
        )
        p.add_argument('-r', '--ref', help='Reference image for compare/census-diff techniques')
        p.add_argument(
            '-d',
            '--fail-on-delta',
            type=float,
            default=None,
            metavar='N',
            help='Exit 1 if any zone colour distance exceeds N (CI gating)',
        )

    # `help` subcommand — prints full module docstring for a technique
    help_parser = sub.add_parser('help', help='Print full docs for a technique')
    help_parser.add_argument('command', nargs='?', help='Technique name')

    # `rfc` subcommand — prints the full GUX RFC
    sub.add_parser('rfc', help='Print the full GUX RFC')

    return parser


def _print_help(command: str | None) -> None:
    """Print full module docstring for a technique."""
    techniques = registry.all_techniques()

    if command is None:
        print('Available techniques:\n')
        for name, tech in sorted(techniques.items()):
            mod = _load_technique_module(name)
            short = (mod.__doc__ or '').strip().splitlines()[0] if (mod.__doc__ or '').strip() else tech.help
            print(f'  {name:<14} {short}')
        print('\nRun: gux-tool help <technique> for full docs.')
        return

    if command not in techniques:
        print(f'Unknown technique: {command}', file=sys.stderr)
        print(f'Available: {", ".join(sorted(techniques))}', file=sys.stderr)
        sys.exit(1)

    mod = _load_technique_module(command)
    doc = (mod.__doc__ or '').strip()
    if not doc:
        print(f'(No module docs for {command!r})')
        return
    print(doc)


def _print_rfc() -> None:
    """Print the full GUX RFC (embedded at build time via make generate-rfc)."""
    from gux_checker.core._rfc_data import get_rfc

    print(get_rfc())


def _check_fail_on_delta(report: Report, threshold: float) -> bool:
    """Return True if any zone colour distance exceeds threshold."""
    failures = []
    for zone_name, zone_data in report.zones.items():
        colours = zone_data.get('techniques', {}).get('colours', {})
        dist = colours.get('distance')
        if dist is not None and dist > threshold:
            failures.append((zone_name, dist))

    if failures:
        print(f'\nFAIL: {len(failures)} zone(s) exceeded delta threshold {threshold}:')
        for zone_name, dist in failures:
            print(f'  {zone_name}: Δ={dist}')
        return True
    return False


def _load_zones(image: Image.Image, args: argparse.Namespace) -> list[ZoneImage]:
    """Load zones from .gux spec, or treat whole image as one zone."""
    if args.gux:
        spec = parse_gux_file(args.gux)
        zones = []
        for gz in spec.zones:
            x1, y1, x2, y2 = gz.bounds
            crop = image.crop((x1, y1, x2, y2))
            zones.append(
                ZoneImage(
                    name=gz.name,
                    bounds=gz.bounds,
                    image=crop,
                    expected_bg=gz.expected_bg,
                    doc=gz.doc,
                    assertions=gz.assertions,
                )
            )
        return zones
    else:
        return [
            ZoneImage(
                name='full',
                bounds=(0, 0, image.width, image.height),
                image=image,
            )
        ]


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Load .env before anything else — OS env vars always win
    env_path = load_env(env_file=getattr(args, 'env_file', None))
    if env_path:
        print(f'gux-tool: loaded {env_path}', file=sys.stderr)

    if not args.technique:
        parser.print_help()
        sys.exit(1)

    # Handle `help` subcommand
    if args.technique == 'help':
        _print_help(getattr(args, 'command', None))
        return

    # Handle `rfc` subcommand
    if args.technique == 'rfc':
        _print_rfc()
        return

    # Load image
    if not os.path.isfile(args.image):
        print(f'Error: image not found: {args.image}', file=sys.stderr)
        sys.exit(1)

    image = Image.open(args.image).convert('RGB')

    # Build zones
    zones = _load_zones(image, args)

    # Build report
    report = Report(
        image_path=args.image,
        image_width=image.width,
        image_height=image.height,
        gux_path=args.gux,
    )
    for z in zones:
        report.set_bounds(z.name, z.bounds)

    # Run technique
    tech = registry.get(args.technique)
    tech.execute(zones, report, args)

    # Output
    if args.technique == 'verify':
        pass  # verify prints its own output
    elif args.json:
        print(format_json(report))
    else:
        print(format_text(report, gux_path=args.gux))

    # CI gate — must happen after output so report is visible even on failure
    threshold = getattr(args, 'fail_on_delta', None)
    if threshold is not None and _check_fail_on_delta(report, threshold):
        sys.exit(1)


if __name__ == '__main__':
    main()
