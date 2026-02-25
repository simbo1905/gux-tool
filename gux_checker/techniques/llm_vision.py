"""Send zone crop images to a vision-capable LLM. OCR, describe, or interrogate.

Uses the same provider config pattern as verify: NAME_API_KEY + NAME_API_URL.
Model defaults to a known vision-capable model for the provider.

Default prompt: "OCR this image. Return only the text you see."

Use --list-models to see vision-capable models for your provider.
Use --prime-rfc to prepend the GUX RFC to the prompt (context for the model).

Model defaults:
  groq     meta-llama/llama-4-maverick-17b-128e-instruct
  mistral  mistral-medium-2505

Example:
    # List vision models for your provider
    GROQ_API_KEY=... gux-tool llm_vision --provider groq --list-models

    # OCR all zones (default prompt)
    GROQ_API_KEY=... gux-tool llm_vision ./tmp shot.png --gux page.gux --provider groq

    # Ask a custom question about each zone
    MISTRAL_API_KEY=... gux-tool llm_vision ./tmp shot.png --gux page.gux \\
        --provider mistral --prompt "Does this look like a bar chart?"

    # Prime with RFC so model understands GUX context
    GROQ_API_KEY=... gux-tool llm_vision ./tmp shot.png --gux page.gux \\
        --provider groq --prime-rfc \\
        --prompt "Does this zone match what the GUX spec describes?"
"""

import base64
import io
import json
import os
import sys
import time
from typing import Any

from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='llm_vision',
    help='Send zone crops to a vision LLM. OCR, describe, or interrogate. Use --list-models.',
)

DEFAULT_PROMPT = 'OCR this image. Return only the text you see, nothing else.'

_DEFAULT_VISION_MODELS: dict[str, str] = {
    'groq': 'meta-llama/llama-4-maverick-17b-128e-instruct',
    'mistral': 'mistral-medium-2505',
    'openai': 'gpt-4o-mini',
}

_MODEL_CACHE_TTL = 3600  # seconds


def _resolve_provider(provider: str, explicit_key: str | None) -> tuple[str, str, str]:
    """Resolve (api_key, api_url, model) for vision calls."""
    env_prefix = provider.upper()
    api_key = explicit_key or os.environ.get(f'{env_prefix}_API_KEY') or os.environ.get('GUX_API_KEY') or ''
    api_url = os.environ.get(f'{env_prefix}_API_URL') or _get_default_url(provider)
    model = os.environ.get(f'{env_prefix}_MODEL') or _DEFAULT_VISION_MODELS.get(provider, '')
    return api_key, api_url, model


def _get_default_url(provider: str) -> str:
    defaults = {
        'groq': 'https://api.groq.com/openai/v1',
        'mistral': 'https://api.mistral.ai/v1',
        'openai': 'https://api.openai.com/v1',
    }
    return defaults.get(provider, '')


def _cache_path(tmp_dir: str, provider: str) -> str:
    return os.path.join(tmp_dir, f'llm_vision_models_{provider}.json')


def _list_models(api_key: str, api_url: str, provider: str, tmp_dir: str) -> list[str]:
    """Fetch and cache model list. Filter to likely vision-capable ones."""
    cache = _cache_path(tmp_dir, provider)
    if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < _MODEL_CACHE_TTL:
        with open(cache) as f:
            return json.load(f)

    try:
        import openai  # type: ignore[import-untyped]
    except ImportError:
        print('llm_vision: pip install openai (or uv add openai)', file=sys.stderr)
        return []

    client = openai.OpenAI(api_key=api_key, base_url=api_url)
    try:
        models = client.models.list()
        all_ids = [m.id for m in models.data]
    except Exception as e:
        print(f'llm_vision: failed to fetch models: {e}', file=sys.stderr)
        return []

    # Filter to likely vision-capable models
    vision_keywords = ['vision', 'llama-4', 'maverick', 'scout', 'medium', 'gpt-4o', 'pixtral', 'kimi']
    vision_models = [m for m in all_ids if any(kw in m.lower() for kw in vision_keywords)]

    # If nothing matched the heuristic, return all
    result = vision_models if vision_models else all_ids

    os.makedirs(tmp_dir, exist_ok=True)
    with open(cache, 'w') as f:
        json.dump(result, f)

    return result


def _image_to_base64(image: Any) -> str:
    """Convert PIL Image to base64-encoded PNG string."""
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def _call_vision(api_key: str, api_url: str, model: str, image: Any, prompt: str) -> str:
    """Send image + prompt to vision model. Returns response text."""
    try:
        import openai  # type: ignore[import-untyped]
    except ImportError:
        return 'error: pip install openai (or uv add openai)'

    b64 = _image_to_base64(image)
    client = openai.OpenAI(api_key=api_key, base_url=api_url)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{b64}'}},
                        {'type': 'text', 'text': prompt},
                    ],
                }
            ],
        )
        return response.choices[0].message.content or ''
    except Exception as e:
        return f'error: {e}'


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    provider = (getattr(args, 'provider', None) or 'groq').lower()
    explicit_key = getattr(args, 'api_key', None)
    api_key, api_url, model = _resolve_provider(provider, explicit_key)

    tmp_dir = getattr(args, 'tmp_dir', '.tmp')
    os.makedirs(tmp_dir, exist_ok=True)

    # --list-models: print and exit
    if getattr(args, 'list_models', False):
        if not api_key:
            print(f'llm_vision: set {provider.upper()}_API_KEY or GUX_API_KEY', file=sys.stderr)
            sys.exit(1)
        models = _list_models(api_key, api_url, provider, tmp_dir)
        print(f'Vision-capable models for {provider} ({api_url}):')
        for m in models:
            marker = ' ◀ default' if m == model else ''
            print(f'  {m}{marker}')
        return

    if not api_key:
        print(f'llm_vision: set {provider.upper()}_API_KEY or GUX_API_KEY', file=sys.stderr)
        return

    if not api_url:
        print(f'llm_vision: set {provider.upper()}_API_URL', file=sys.stderr)
        return

    if not model:
        print(f'llm_vision: set {provider.upper()}_MODEL or use a known provider', file=sys.stderr)
        return

    # Build prompt
    user_prompt = getattr(args, 'prompt', None) or DEFAULT_PROMPT

    if getattr(args, 'prime_rfc', False):
        from gux_checker.core._rfc_data import get_rfc

        user_prompt = (
            'Here is the GUX specification language RFC so you understand '
            'what a GUX zone is and what we are trying to verify:\n\n'
            f'{get_rfc()}\n\n'
            f'Now, here is a cropped zone image from a screenshot.\n{user_prompt}'
        )

    print(f'llm_vision: provider={provider}  model={model}  url={api_url}')

    for zone in zones:
        result = _call_vision(api_key, api_url, model, zone.image, user_prompt)
        report.add(zone.name, 'llm_vision', {'text': result, 'model': model, 'provider': provider})
