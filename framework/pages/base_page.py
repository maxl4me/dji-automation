"""Generic Page Object base class.

Rules for this file:
  * Domain-free. No DJI-specific logic here. If a method references dji.com
    or a DJI selector, it belongs in a concrete page object, not here.
  * All waits are explicit and network-aware. No time.sleep.
  * Highlighting is optional and gated on [debug] highlight_elements in config.
  * Methods accept either a CSS string or a Playwright Locator; helpers resolve.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

from framework.config import ConfigReader
from framework.logger import get_logger

log = get_logger(__name__)

# Type alias: pages can pass a raw CSS string or a pre-built Locator.
# Pre-built Locators are preferred for role-based selectors (e.g. page.get_by_role).
LocatorTarget = str | Locator

_DEFAULT_TIMEOUT_MS = ConfigReader.read_int("timeouts", "default_timeout_ms")
_TEXT_TIMEOUT_MS = ConfigReader.read_int("timeouts", "text_timeout_ms")
_HIGHLIGHT = ConfigReader.read_bool("debug", "highlight_elements")


class BasePage:
    """Shared helpers for all page objects."""

    def __init__(self, page: Page) -> None:
        self.page = page

    # ------------------------------------------------------------------ helpers

    def _resolve(self, target: LocatorTarget) -> Locator:
        """Accept either a CSS string or a Locator; always return a Locator."""
        return target if isinstance(target, Locator) else self.page.locator(target)

    def _maybe_highlight(self, locator: Locator) -> None:
        """Debug aid — silently no-op when disabled or when the element can't be highlighted."""
        if not _HIGHLIGHT:
            return
        try:
            locator.highlight()
        except Exception:  # highlighting is decorative, never blocks a test
            pass

    # ------------------------------------------------------------------ actions

    def click(self, target: LocatorTarget) -> None:
        locator = self._resolve(target)
        self._maybe_highlight(locator)
        locator.click()

    def fill(self, target: LocatorTarget, text: str) -> None:
        locator = self._resolve(target)
        self._maybe_highlight(locator)
        locator.fill(text)

    def press(self, target: LocatorTarget, key: str) -> None:
        locator = self._resolve(target)
        self._maybe_highlight(locator)
        locator.press(key)

    def select_option(self, target: LocatorTarget, value: str) -> None:
        locator = self._resolve(target)
        self._maybe_highlight(locator)
        locator.select_option(value=value)

    # ------------------------------------------------------------------ queries

    def inner_text(self, target: LocatorTarget) -> str:
        locator = self._resolve(target)
        self._maybe_highlight(locator)
        return locator.inner_text()

    def is_visible(self, target: LocatorTarget, timeout_ms: int | None = None) -> bool:
        """True if the element becomes visible within the timeout. Never raises."""
        locator = self._resolve(target)
        timeout = timeout_ms if timeout_ms is not None else _TEXT_TIMEOUT_MS
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def contains_text(self, text: str, timeout_ms: int | None = None) -> bool:
        """True if any visible element contains the given text within the timeout."""
        timeout = timeout_ms if timeout_ms is not None else _TEXT_TIMEOUT_MS
        try:
            self.page.get_by_text(text).first.wait_for(state="visible", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    # ------------------------------------------------------------------ waits

    def wait_for_visible(self, target: LocatorTarget, timeout_ms: int | None = None) -> None:
        """Raise if not visible in time. Use when the test *requires* the element."""
        locator = self._resolve(target)
        timeout = timeout_ms if timeout_ms is not None else _DEFAULT_TIMEOUT_MS
        locator.wait_for(state="visible", timeout=timeout)
        self._maybe_highlight(locator)
