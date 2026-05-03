"""DJI Global homepage.

Owns the homepage's own elements (main nav, hero) and provides an entry
point to the header search overlay. The overlay itself is a Component
(framework/components/search_overlay.py) because it appears across pages.
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
        self._main_nav_link = page.get_by_role("link", name="Camera Drones", exact=True).first

        # Header search trigger. The <a> tag has aria-label="Search" — the
        # most stable hook because aria-label is an accessibility commitment
        # that doesn't change with visual redesigns.
        self._search_trigger = page.get_by_role("link", name="Search", exact=True)

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

    @allure.step("Open header search overlay")
    def open_search_overlay(self) -> SearchOverlay:
        """Click the header magnifying glass and return the overlay component."""
        self.click(self._search_trigger)
        overlay = SearchOverlay(self.page)
        # Wait for the input to be ready before returning, so callers can
        # immediately type without an extra wait_for in every test.
        overlay.wait_for_visible(overlay._search_input)
        return overlay

    def page_title(self) -> str:
        return self.page.title()

    def current_url(self) -> str:
        return self.page.url
