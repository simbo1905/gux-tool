"""Technique auto-discovery and registration.

Scans gux_checker/techniques/ for modules that define a `technique` object
of type Technique. Collects them into a dict keyed by name.

Handles both normal Python (pkgutil.iter_modules) and frozen PyInstaller
binaries (where iter_modules returns nothing — falls back to explicit
imports from techniques/__init__.py).
"""

import importlib
import pkgutil

from gux_checker.core.types import Technique

_registry: dict[str, Technique] = {}

# Known technique module names — fallback for frozen binaries
_TECHNIQUE_MODULES = [
    'all',
    'census',
    'census_diff',
    'colours',
    'compare',
    'lines',
    'ocr',
    'regions',
    'verify',
    'zones',
]


def discover() -> dict[str, Technique]:
    """Import all technique modules and return the registry."""
    if _registry:
        return _registry

    import gux_checker.techniques as pkg

    # Try pkgutil first (works in normal Python)
    found_modules = [
        modname for _importer, modname, _ispkg in pkgutil.iter_modules(pkg.__path__) if not modname.startswith('_')
    ]

    # Frozen binary fallback: pkgutil finds nothing, use known list
    if not found_modules:
        found_modules = _TECHNIQUE_MODULES

    for modname in found_modules:
        module = importlib.import_module(f'gux_checker.techniques.{modname}')
        tech = getattr(module, 'technique', None)
        if isinstance(tech, Technique):
            _registry[tech.name] = tech

    return _registry


def get(name: str) -> Technique:
    """Get a technique by name."""
    reg = discover()
    if name not in reg:
        raise KeyError(f'Unknown technique: {name}. Available: {", ".join(sorted(reg))}')
    return reg[name]


def all_techniques() -> dict[str, Technique]:
    """Return all registered techniques."""
    return discover()
