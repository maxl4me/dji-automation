"""DJI Global search results page (the page at /search?q=...).

Why it's a page object and not a component: it's a destination URL with
its own DOM structure and concerns (result count, empty state, search
input). Distinct from the homepage's search overlay.

A note on synchronization (worth reading once):
  DJI initially renders a product-tab skeleton on every search results
  page. The JS then either fills the skeleton with a real result count
  OR replaces the entire results region with a .no-data block. So we
  cannot just wait for "any tab is visible" — that's true even before
  the backend answers. We have to wait for the DEFINITIVE signals:
    - The product tab has a count text inside (not just the skeleton)
    - OR the .no-data block has appeared
  Once either is true, the backend has answered and we can assert.
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

# Format: '(17)' — DJI puts parentheses around the count.
_COUNT_PATTERN = re.compile(r"\((\d+)\)")

# Returns true when DJI's backend has answered: either a populated count
# is visible, or the no-data block has appeared.
_SETTLE_PREDICATE = """() => {
    const countSpan = document.querySelector('li.tab[data-item="product"] span.num');
    const populatedCount =
        countSpan && countSpan.offsetHeight > 0 && /\\(\\d+\\)/.test(countSpan.textContent);
    const noData = document.querySelector('div.no-data');
    const noDataVisible = noData && noData.offsetHeight > 0;
    return populatedCount || noDataVisible;
}"""


class SearchResultsPage(BasePage):
    """Results page at /global/search?q=... — populated either with products or empty state."""

    _base_url = ConfigReader.read_str("app", "base_url")
    _navigation_timeout = ConfigReader.read_int("timeouts", "navigation_timeout_ms")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Search input on the results page (different element from overlay input).
        self._search_input = page.locator('form#search-from input[name="q"]')

        # Result tab. data-item is a stable framework attribute.
        self._product_tab = page.locator('li.tab[data-item="product"]')
        self._product_count_text = self._product_tab.locator("span.num")

    # ---------------------------------------------------------------- waits

    @allure.step("Wait for results to settle")
    def wait_for_results_settled(self) -> None:
        """Wait until DJI's backend has answered: populated count OR no-data block.

        See module docstring for why we can't just wait on the product tab.
        """
        log.info("Waiting for results to settle")
        self.page.wait_for_function(_SETTLE_PREDICATE, timeout=self._navigation_timeout)

    # ---------------------------------------------------------------- navigation

    @allure.step("Open search results directly: {query}")
    def goto(self, query: str) -> None:
        """Direct URL navigation. Skips the overlay entirely."""
        url = f"{self._base_url}/search?q={quote(query)}"
        log.info("Navigating directly to %s", url)
        self.page.goto(url, wait_until="domcontentloaded", timeout=self._navigation_timeout)
        # Always settle before returning — callers shouldn't have to remember.
        self.wait_for_results_settled()

    # ---------------------------------------------------------------- queries

    @allure.step("Read product result count")
    def product_count(self) -> int:
        """Return the integer in 'PRODUCT (N)'. Returns 0 if no product tab exists.

        Assumes wait_for_results_settled has been called (goto() does this).
        """
        # If no-data is visible, there are no products — return 0 without
        # trying to parse a tab that won't be populated.
        if self._eval_offset_height("div.no-data") > 0:
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
        """True if the empty-state block is visible.

        Assumes wait_for_results_settled has already been called. Reads the
        layout state directly via offsetHeight (the ground-truth signal —
        non-zero means the browser laid out the element).
        """
        return self._eval_offset_height("div.no-data") > 0

    @allure.step("Read search input value")
    def search_input_value(self) -> str:
        """Read the input's `value` attribute — what the URL query produced."""
        self.wait_for_visible(self._search_input)
        return self._search_input.input_value()

    def current_url(self) -> str:
        return self.page.url

    # ---------------------------------------------------------------- internal

    def _eval_offset_height(self, selector: str) -> int:
        """Return the element's offsetHeight (0 if absent or not laid out)."""
        return int(
            self.page.evaluate(
                "(sel) => { const el = document.querySelector(sel); return el ? el.offsetHeight : 0; }",
                selector,
            )
        )
