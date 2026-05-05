"""Search overlay component.

This is a *component* (not a page) because it appears on top of whatever
page the user is on, rather than being a destination. It's a UI fragment
that's invoked from anywhere the site header is visible.

A note on submission behavior:
  The overlay's <form> has target="_blank" in markup, suggesting submission
  would open a new tab. In practice, programmatic Enter-key submission via
  Playwright navigates the SAME tab — which is what we observe at runtime.
  We trust runtime behavior over markup and treat submission as a same-tab
  navigation. This is verified by the test suite.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from framework.config import ConfigReader
from framework.logger import get_logger
from framework.pages.base_page import BasePage

log = get_logger(__name__)


class SearchOverlay(BasePage):
    """Header search overlay. Open it via HomePage.open_search_overlay()."""

    _navigation_timeout = ConfigReader.read_int("timeouts", "navigation_timeout_ms")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._search_form = page.locator('form[role="search"]')
        self._search_input = self._search_form.locator('input[name="q"]')

    @allure.step("Type search query: {query}")
    def type_query(self, query: str) -> None:
        log.info("Typing search query: %s", query)
        # wait_for_visible because the overlay animates in; if we fill too
        # early, focus may be lost mid-animation and the keystrokes drop.
        self.wait_for_visible(self._search_input)
        self.fill(self._search_input, query)

    @allure.step("Submit search and wait for results URL")
    def submit(self) -> None:
        """Press Enter to submit. Caller should then wait for the results URL.

        Note: the form has target="_blank" in markup, but programmatic
        submission stays in the same tab. We rely on the same-tab behavior.

        wait_until="domcontentloaded" matches the rest of the framework —
        we wait only until the DOM is parsed and JS can run, not for every
        last analytics script and image to finish (the 'load' event), which
        on DJI's media-heavy results page can take 30+ seconds.
        """
        log.info("Submitting search (same-tab navigation)")
        self.press(self._search_input, "Enter")
        self.page.wait_for_url(
            "**/search?**",
            wait_until="domcontentloaded",
            timeout=self._navigation_timeout,
        )

    def is_open(self) -> bool:
        return self.is_visible(self._search_input)
