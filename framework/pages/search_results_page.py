"""DJI search results page (`/global/search?q=...`).

Distinct page object because it has its own URL and DOM, separate from
the overlay. Supports two entry points:

  1. Arriving via the overlay (after submitting) — caller passes the new
     Page from BrowserContext.expect_page().
  2. Direct URL navigation via `goto(query)` — useful for tests that
     focus on results behavior without re-clicking the overlay.

Result tabs (PRODUCT, NEWS, etc.) use a stable data attribute
`data-item="<category>"`, which we use as the primary locator. The count
text is `(17)` style — note the parentheses are part of the text.
"""

from __future__ import annotations

import re
from urllib.parse import quote

import allure
from playwright.sync_api import Page

from framework.config import ConfigReader
from framework.logger import get_logger
from framework.pages.base_page import BasePage

log = get_logger(__name__)

# Matches "(17)" or "( 17 )" — pull out the integer regardless of whitespace.
_COUNT_PATTERN = re.compile(r"\((\d+)\)")


class SearchResultsPage(BasePage):
    """`/global/search?q=...` page."""

    _base_url = ConfigReader.read_str("app", "base_url").rstrip("/")
    _navigation_timeout = ConfigReader.read_int("timeouts", "navigation_timeout_ms")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Search input on the results page (different from overlay input).
        # `name="q"` again, but inside <form id="search-from">.
        self._search_input = page.locator('form#search-from input[name="q"]')

        # Result category tabs. data-item is a stable framework attribute,
        # far less brittle than CSS class selectors that include build hashes.
        self._product_tab = page.locator('li.tab[data-item="product"]')
        self._product_count_text = self._product_tab.locator("span.num")

        # No-results container. The empty-state UI is rendered by JS *after*
        # initial DOM load — anchoring on the semantic class .no-data-title
        # is more reliable than text matching for dynamically inserted content.
        # The class name is stable (no build hash), so this is durable.
        self._no_results_heading = page.locator("div.no-data-title")

    @allure.step("Open search results directly: {query}")
    def goto(self, query: str) -> None:
        """Direct URL navigation. Skips the overlay entirely."""
        url = f"{self._base_url}/search?q={quote(query)}"
        log.info("Navigating directly to %s", url)
        self.page.goto(url, wait_until="domcontentloaded", timeout=self._navigation_timeout)

    @allure.step("Read product result count")
    def product_count(self) -> int:
        """Return the integer in 'PRODUCT (N)'. Returns 0 if the tab isn't visible."""
        if not self.is_visible(self._product_tab):
            return 0
        text = self.inner_text(self._product_count_text)
        match = _COUNT_PATTERN.search(text)
        if not match:
            raise ValueError(
                f"Could not parse product count from {text!r}. "
                "DJI may have changed the count format; update _COUNT_PATTERN."
            )
        return int(match.group(1))

    @allure.step("Check no-results state")
    def is_no_results_shown(self) -> bool:
        return self.is_visible(self._no_results_heading)

    @allure.step("Read search input value")
    def search_input_value(self) -> str:
        """Read the input's `value` attribute — what the URL query produced."""
        self.wait_for_visible(self._search_input)
        return self._search_input.input_value()

    def current_url(self) -> str:
        return self.page.url
