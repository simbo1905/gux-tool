"""Send extraction report + GUX spec to an LLM API for pass/fail verdict.

Runs 'all' first to produce a structured JSON report. Then sends the
report + the .gux spec text to an LLM and asks it to compare each zone
and state PASS/FAIL with a one-line reason.

The LLM never sees the screenshot pixels. It reads numbers.

## Provider configuration

Uses any OpenAI-compatible endpoint. Set env vars (in .env or environment):

    {PROVIDER}_API_KEY   — required
    {PROVIDER}_API_URL   — required (base URL of the OpenAI-compatible API)
    {PROVIDER}_MODEL     — optional, overrides the default model

Built-in provider defaults:

    mistral   MISTRAL_API_KEY   MISTRAL_API_URL=https://api.mistral.ai/v1
              default model: mistral-medium-2505

    groq      GROQ_API_KEY      GROQ_API_URL=https://api.groq.com/openai/v1
              default model: llama-3.3-70b-versatile

Any other OpenAI-compatible endpoint:

    MYMODEL_API_KEY=...
    MYMODEL_API_URL=http://localhost:11434/v1
    MYMODEL_MODEL=llama3
    uv run gux-tool verify ./tmp shot.png --gux page.gux --provider mymodel

At startup, prints the resolved provider, model and URL for confirmation.

Requires --gux. API key taken from env or --api-key flag.

Example:
    MISTRAL_API_KEY=... uv run gux-tool verify ./tmp shot.png --gux page.gux --provider mistral
    GROQ_API_KEY=...    uv run gux-tool verify ./tmp shot.png --gux page.gux --provider groq
"""

import os
import sys

from gux_checker.core.report import format_json
from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='verify',
    help='Run all techniques, then send report + .gux spec to an LLM for pass/fail verdict.',
)

# Default API URLs for known providers
_DEFAULT_URLS: dict[str, str] = {
    'mistral': 'https://api.mistral.ai/v1',
    'groq': 'https://api.groq.com/openai/v1',
    'openai': 'https://api.openai.com/v1',
}

# Default models for known providers
_DEFAULT_MODELS: dict[str, str] = {
    'mistral': 'mistral-medium-2505',
    'groq': 'llama-3.3-70b-versatile',
    'openai': 'gpt-4o-mini',
}

PROMPT_TEMPLATE = """Here is a GUX visual spec and a structured extraction report from a screenshot.
Compare each zone's extracted data against the spec.
For each zone, state PASS or FAIL with a one-line reason.
Do not ask for the image. All the data you need is in the report.

## GUX Spec

{gux_text}

## Extraction Report

{report_json}
"""


def _resolve_provider(provider: str, explicit_key: str | None) -> tuple[str, str, str]:
    """Resolve (api_key, api_url, model) from env vars for the given provider name."""
    env_prefix = provider.upper()
    api_key = explicit_key or os.environ.get(f'{env_prefix}_API_KEY') or os.environ.get('GUX_API_KEY') or ''
    api_url = os.environ.get(f'{env_prefix}_API_URL') or _DEFAULT_URLS.get(provider, '')
    model = os.environ.get(f'{env_prefix}_MODEL') or _DEFAULT_MODELS.get(provider, 'gpt-4o-mini')
    return api_key, api_url, model


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    from gux_checker.registry import get as get_technique

    all_tech = get_technique('all')
    all_tech.execute(zones, report, args)

    if not hasattr(args, 'gux') or not args.gux:
        print('verify: --gux spec file required', file=sys.stderr)
        return

    provider = (getattr(args, 'provider', None) or 'mistral').lower()
    explicit_key = getattr(args, 'api_key', None)

    api_key, api_url, model = _resolve_provider(provider, explicit_key)

    if not api_key:
        env_prefix = provider.upper()
        print(f'verify: no API key. Set {env_prefix}_API_KEY or GUX_API_KEY.', file=sys.stderr)
        return

    if not api_url:
        print(f'verify: no API URL. Set {provider.upper()}_API_URL.', file=sys.stderr)
        return

    print(f'verify: provider={provider}  model={model}  url={api_url}')

    with open(args.gux, encoding='utf-8') as f:
        gux_text = f.read()

    prompt = PROMPT_TEMPLATE.format(gux_text=gux_text, report_json=format_json(report))
    _call_openai_compat(api_key, api_url, model, prompt)


def _call_openai_compat(api_key: str, api_url: str, model: str, prompt: str) -> None:
    """Call any OpenAI-compatible endpoint."""
    try:
        import openai  # type: ignore[import-untyped]
    except ImportError:
        print('verify: pip install openai (or uv add openai)', file=sys.stderr)
        return

    client = openai.OpenAI(api_key=api_key, base_url=api_url)
    response = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
    )
    print(response.choices[0].message.content)
