"""DJI Global homepage.

Owns the homepage's own elements (main nav, hero, region indicator) and
provides an entry point to the header search overlay. The overlay itself
is a Component (framework/components/search_overlay.py) because it appears
across pages.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from framework.components.search_overlay import SearchOverlay
from framework.config import ConfigReader
from framework.logger import get_logger
from framework.pages.base_page import BasePage

log = get_logger(__name__)


class HomePage(BasePage):
    """DJI Global landing page."""

    _base_url = ConfigReader.read_str("app", "base_url")
    _navigation_timeout = ConfigReader.read_int("timeouts", "navigation_timeout_ms")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Anchor on a top-level product category nav link. DJI's <header>
        # element does NOT carry role=banner (verified by live inspection),
        # so we anchor on something we can actually see on the page.
        # "Camera Drones" is a primary product line — stable across
        # marketing redesigns far more than CSS class names would be.
        #
        # NOTE: we locate page-wide, NOT scoped to <header>. Recon showed
        # there is effectively no usable single <header> element wrapping
        # the visible nav (document.querySelector("header") returned null
        # in the test environment). The aria-label is unique page-wide,
        # which is all the disambiguation we need.
        self._main_nav_link = page.get_by_role("link", name="Camera Drones", exact=True).first

        # Header search trigger. The <a> tag has aria-label="Search" — the
        # most stable hook because aria-label is an accessibility commitment
        # that doesn't change with visual redesigns.
        self._search_trigger = page.get_by_role("link", name="Search", exact=True)

        # Region indicator — the "Other Regions" control. Anchor on the
        # visible container div.language-box. Recon's DOM dump also showed a
        # bare <span> with exact text "Other Regions", but an in-Playwright
        # probe proved that span is_visible=False — it lives in the hidden
        # language flyout. div.language-box is the visible chrome the user
        # actually sees (probe: count=1, is_visible=True). The class is
        # semantic ('language-box'), not a build hash, so it's a legitimate
        # CSS anchor here. Verified in the test environment (2026-05-28).
        self._region_indicator = page.locator("div.language-box").first

    @allure.step("Open DJI Global homepage")
    def open(self) -> None:
        log.info("Navigating to %s", self._base_url)
        self.page.goto(
            self._base_url,
            wait_until="domcontentloaded",
            timeout=self._navigation_timeout,
        )

    @allure.step("Verify homepage main navigation is visible")
    def main_nav_is_visible(self) -> bool:
        return self.is_visible(self._main_nav_link)

    @allure.step("Verify region indicator is visible")
    def region_indicator_is_visible(self) -> bool:
        """True if the 'Other Regions' switcher is visible on the homepage."""
        return self.is_visible(self._region_indicator)

    @allure.step("Open header search overlay")
    def open_search_overlay(self) -> SearchOverlay:
        """Click the header magnifying glass and return the overlay component."""
        self.click(self._search_trigger)
        overlay = SearchOverlay(self.page)
        # Wait for the input to be ready before returning, so callers can
        # immediately type without an extra wait_for in every test.
        overlay.wait_for_visible(overlay._search_input)
        return overlay

    @allure.step("Click nav link: {name}")
    def click_nav_link(self, name: str, href_contains: str | None = None) -> None:
        """Click a top-level nav link by accessible name.

        Located page-wide by accessible name (not <header>-scoped; there is
        no usable single <header> wrapping the nav — verified by recon).
        The aria-label is unique page-wide for most nav links.

        Some nav names appear on more than one link (e.g. "Support" exists
        as both a header nav link with `from=nav` and a body link with
        `from=homepage`). For those, pass href_contains to pin the exact
        link. Navigation is same-tab for all current nav targets.

        Args:
            name: Exact accessible name of the link (e.g. "Camera Drones",
                  "Where to Buy", "Support").
            href_contains: Optional substring of the target href, used to
                  disambiguate when more than one link shares the same
                  accessible name.
        """
        if href_contains is not None:
            # Disambiguate by the link's own href. Recon shows the href
            # fragment (e.g. "from=nav") is the unique disambiguator.
            link = self.page.locator(f'a[href*="{href_contains}"]').first
        else:
            link = self.page.get_by_role("link", name=name, exact=True).first
        self.wait_for_visible(link)
        log.info("Clicking nav link: %s", name)
        with self.page.expect_navigation(
            wait_until="domcontentloaded",
            timeout=self._navigation_timeout,
        ):
            self.click(link)

    def page_title(self) -> str:
        return self.page.title()

    def current_url(self) -> str:
        return self.page.url
