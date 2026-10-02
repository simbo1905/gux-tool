"""Locate a Chrome/Chromium binary for headless screenshots.

The integration tests skip themselves when no browser is found, so detection has
to work on macOS and Windows as well as Linux. Override with the CHROME
environment variable to pin a specific binary.

Keep CHROME_CANDIDATES in sync with the candidate list in the Makefile.
"""

import os
import shutil
from pathlib import Path

CHROME_ENV = 'CHROME'

CHROME_CANDIDATES = (
    'google-chrome-stable',
    'google-chrome',
    'chromium',
    'chromium-browser',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
)


def find_chrome() -> str | None:
    """Return a path to a Chrome binary, or None if none can be found."""
    override = os.environ.get(CHROME_ENV)
    if override:
        return override if _is_runnable(override) else None

    for candidate in CHROME_CANDIDATES:
        if _is_runnable(candidate):
            return candidate
    return None


def _is_runnable(candidate: str) -> bool:
    """True if candidate is an executable file or a name found on PATH."""
    if Path(candidate).is_file():
        return os.access(candidate, os.X_OK)
    return shutil.which(candidate) is not None
