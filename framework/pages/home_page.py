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
        # Role-based locator. Preferred over CSS because the header's
        # hashed class names will change with every DJI deployment, but
        # role=banner (the <header> element) is stable by spec.
        self._header = page.get_by_role("banner").first

    @allure.step("Open DJI Global homepage")
    def open(self) -> None:
        log.info("Navigating to %s", self._base_url)
        self.page.goto(
            self._base_url,
            wait_until="domcontentloaded",
            timeout=self._navigation_timeout,
        )

    @allure.step("Verify homepage header is visible")
    def header_is_visible(self) -> bool:
        return self.is_visible(self._header)

    def current_url(self) -> str:
        return self.page.url
