"""DJI Store homepage (store.dji.com).

Distinct from the marketing-site HomePage: different subdomain, different
navigation, different DOM. Entry point for the cart flow.

Region behavior (verified by recon, 2026-05-19):
  The store is NOT IP-redirected the way the marketing site is. It
  defaults every visitor to the US store regardless of source IP. The
  server sets a `region=US` cookie on first load; a separate
  `ip_region=IL` cookie records the real IP-region but is deliberately
  NOT acted upon. A fresh Playwright context (no cookies) therefore
  lands on the US store deterministically — locally and in CI alike.
  This is why the cart flow pins the US store and asserts region as a
  FAIL-LOUD guard rather than tolerating drift.

Cart isolation note:
  The cart is keyed to a `cart_uuid` cookie. A fresh context has no
  such cookie, so the server issues a new one — each test's context
  starts with its own empty cart automatically. Cross-test cart leakage
  is prevented by the existing per-test context fixture, not app logic.

Region indicator text "United States (English / $ USD)" verified
present in every store screenshot during recon.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from framework.components.cookie_consent import CookieConsent
from framework.config import ConfigReader
from framework.logger import get_logger
from framework.pages.base_page import BasePage

log = get_logger(__name__)


class StoreHomePage(BasePage):
    """Landing page for store.dji.com (defaults to the US store)."""

    _store_base_url = ConfigReader.read_str("app", "store_base_url")
    _navigation_timeout = ConfigReader.read_int("timeouts", "navigation_timeout_ms")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.cookie_consent = CookieConsent(page)

        # Region indicator in the utility bar: "United States
        # (English / $ USD)". Verified present in all recon screenshots.
        # Matched as a substring; the wrapper has no stable hook.
        self._region_indicator = page.get_by_text("United States", exact=False).first

    @allure.step("Open DJI Store (defaults to US store)")
    def open(self) -> None:
        log.info("Navigating to %s", self._store_base_url)
        self.page.goto(
            self._store_base_url,
            wait_until="domcontentloaded",
            timeout=self._navigation_timeout,
        )
        # Dismiss the privacy banner immediately so later clicks aren't
        # intercepted. Safe no-op if absent.
        self.cookie_consent.dismiss_if_present()

    @allure.step("Assert we are on the US store (region guard)")
    def assert_us_region(self) -> None:
        """Fail loud if the store is not defaulting to US.

        The region guard from the design decision. We do NOT tolerate
        region drift here (unlike the marketing-site tests) because the
        store is not IP-redirected — US is the documented default in
        every environment. If this fails, the store's default behavior
        changed (or a region cookie leaked into this context) and the
        pinning premise needs revisiting; failing loudly surfaces that
        immediately rather than passing against the wrong store.
        """
        assert self.is_visible(self._region_indicator), (
            "Store region indicator does not show 'United States'. The "
            "store may have changed its default-region behavior, or a "
            "region cookie leaked into this context. The cart flow pins "
            "the US store on the premise that it is the default in all "
            "environments — investigate before trusting this run. Check "
            "the Allure trace for the actual region shown."
        )

    def current_url(self) -> str:
        return self.page.url
