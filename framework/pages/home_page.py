"""DJI Global homepage — minimal implementation for the Phase 1 smoke test.

Intentionally small. Only what the smoke test needs. More locators and actions
will be added as we expand coverage in Phase 2+.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

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

    def page_title(self) -> str:
        return self.page.title()

    def current_url(self) -> str:
        return self.page.url
