"""Auto-discovery of technique modules.

Every .py file in this package that defines a `technique` object is
auto-registered by gux_checker.registry.discover().

The explicit imports below ensure PyInstaller includes these modules
in the frozen binary. Without them, pkgutil.iter_modules cannot find
the technique files at runtime.
"""

# PyInstaller hidden imports — keep this list in sync with technique modules
import gux_checker.techniques.all as _all  # noqa: F401
import gux_checker.techniques.census as _census  # noqa: F401
import gux_checker.techniques.census_diff as _census_diff  # noqa: F401
import gux_checker.techniques.colours as _colours  # noqa: F401
import gux_checker.techniques.compare as _compare  # noqa: F401
import gux_checker.techniques.lines as _lines  # noqa: F401
import gux_checker.techniques.ocr as _ocr  # noqa: F401
import gux_checker.techniques.regions as _regions  # noqa: F401
import gux_checker.techniques.verify as _verify  # noqa: F401
import gux_checker.techniques.zones as _zones  # noqa: F401
