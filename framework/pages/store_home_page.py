"""DJI Store homepage (store.dji.com).

Distinct from the marketing-site HomePage: different subdomain, different
navigation, different DOM. Entry point for the cart flow.

Region behavior (verified by recon 2026-05-19, corrected 2026-06-01):
  From our LOCAL (Israel) IP the store serves the US store: it sets a
  `region=US` cookie and records the real IP in a separate, unacted-upon
  `ip_region=IL` cookie. A fresh Playwright context lands on the US store
  from Israel deterministically, which is why the cart flow pins the US
  store and asserts region as a FAIL-LOUD guard.

  CORRECTION: the store DOES geo-route by IP. The original "not
  IP-redirected" reading was an Israel-only coincidence (IL happens to
  receive the US store). CI runners get a different regional store
  (observed store.dji.com/uk), so assert_us_region fails there for an
  environmental reason. The store tests are therefore skipped in CI
  (see tests/cart/test_cart.py, STP KI-005) and run locally from Israel.
  The guard below is intentionally NOT weakened — it correctly caught the
  premise violation; the tests are scoped by environment instead.

Cart isolation note:
  The cart is keyed to a `cart_uuid` cookie. A fresh context has no
  such cookie, so the server issues a new one — each test's context
  starts with its own empty cart automatically. Cross-test cart leakage
  is prevented by the existing per-test context fixture, not app logic.

Region indicator text "United States (English / $ USD)" verified
present in every US-store screenshot during recon.
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
    """Landing page for store.dji.com (US store from an Israel IP)."""

    _store_base_url = ConfigReader.read_str("app", "store_base_url")
    _navigation_timeout = ConfigReader.read_int("timeouts", "navigation_timeout_ms")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.cookie_consent = CookieConsent(page)

        # Region indicator in the utility bar: "United States
        # (English / $ USD)". Verified present in all recon screenshots.
        # Matched as a substring; the wrapper has no stable hook.
        self._region_indicator = page.get_by_text("United States", exact=False).first

    @allure.step("Open DJI Store (defaults to US store from Israel IP)")
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
        """Fail loud if the store is not serving US.

        Kept strict on purpose. The store geo-routes by IP (see module
        docstring): from Israel we get the US store, so locally this guard
        holds. It correctly fails on CI runners that get another regional
        store — which is why the store tests are skipped in CI (KI-005)
        rather than this guard being relaxed. If this fails LOCALLY, the
        store's behavior for our IP changed (or a region cookie leaked
        into the context) and the pinning premise needs revisiting;
        failing loudly surfaces that immediately.
        """
        assert self.is_visible(self._region_indicator), (
            "Store region indicator does not show 'United States'. The "
            "store may have changed its behavior for this IP, or a region "
            "cookie leaked into this context. The cart flow pins the US "
            "store (served to our Israel IP); investigate before trusting "
            "this run. Check the Allure trace for the actual region shown."
        )

    def current_url(self) -> str:
        return self.page.url
