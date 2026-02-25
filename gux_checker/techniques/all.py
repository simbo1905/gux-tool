"""Run every extraction technique, combine into a single report.

Runs: colours, zones, census, lines, regions.
Runs census-diff too if --ref is provided.
Skips: ocr (requires system tesseract — run explicitly if needed).
Skips: verify (requires API key — run explicitly).
Skips: compare (use census-diff for ref comparisons in all mode).

Example:
    uv run gux-tool all ./tmp screenshot.png --gux dashboard.gux
    uv run gux-tool all ./tmp screenshot.png --gux dashboard.gux --json
    uv run gux-tool all ./tmp screenshot.png --gux dashboard.gux --fail-on-delta=20
    uv run gux-tool all ./tmp current.png --gux dashboard.gux --ref ref.png
"""

from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='all',
    help='Run every extraction technique (except ocr/verify). Combine into a single report.',
)

# Techniques never run automatically
SKIP = {'all', 'verify', 'ocr', 'compare'}


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    from gux_checker.registry import all_techniques

    has_ref = hasattr(args, 'ref') and args.ref
    for name, tech in sorted(all_techniques().items()):
        if name in SKIP:
            continue
        # census-diff only runs when --ref is provided
        if name == 'census-diff' and not has_ref:
            continue
        tech.execute(zones, report, args)
