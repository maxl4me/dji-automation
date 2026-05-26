"""DJI Store cart page (store.dji.com/cart).

This page object has the strongest recon evidence in the whole flow.
All selectors verified against the LIVE US-store DOM (2026-05-19) via
console queries, not assumed (the earlier image-8 evidence was the /ca
cart; these were re-confirmed on the US store):

  document.querySelector('[data-test-locator="sectionTableRow"]')
    -> <div data-test-locator="sectionTableRow" class="style__row___3Sml5">
       CONFIRMED present on the US cart.

  document.querySelector('button[aria-label="Remove"]')
    -> <button aria-label="Remove" data-test-locator="btnDelete"
              class="style__action___3qiQT">
       CONFIRMED present on the US cart. Two stable hooks:
       aria-label="Remove" (accessible name) AND
       data-test-locator="btnDelete".

  document.querySelector('[data-test-locator="sectionTableRow"]').innerText
    -> 'DJI FPV Remote Controller 3\n\nUSD $199\n\nUSD $199'
       CONFIRMED the product NAME is inside the row's text, which is
       why contains_product() can match by reading row innerText.

Locator priority applied (role/label > data-* > CSS > XPath):
  * Remove button: role=button + name "Remove" (from aria-label) is
    primary; data-test-locator="btnDelete" is the documented fallback.
  * Item row: data-test-locator="sectionTableRow" — a deliberate,
    stable test hook, far better than the hashed sibling class
    style__row___3Sml5 (build-tool output, volatile).

URL: store.dji.com/cart — verified, NO region segment on the US default
store (the /ca/cart from early recon was post region-click).

Known non-issue: the cart page logs a PayPal SDK console error
("zoid destroyed all components") caused by third-party-cookie /
ad-block interference with PayPal's iframe. It is unrelated to cart
add/remove and the cart renders and functions normally. The framework
does not assert on console errors, so this does not affect the test;
documented here so a future "fail on console error" check would not
false-fail this test on an unrelated PayPal/adblock issue.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from framework.components.cookie_consent import CookieConsent
from framework.config import ConfigReader
from framework.logger import get_logger
from framework.pages.base_page import BasePage

log = get_logger(__name__)


class CartPage(BasePage):
    """The shopping cart at /cart on store.dji.com."""

    _store_base_url = ConfigReader.read_str("app", "store_base_url")
    _navigation_timeout = ConfigReader.read_int("timeouts", "navigation_timeout_ms")
    _default_timeout = ConfigReader.read_int("timeouts", "default_timeout_ms")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.cookie_consent = CookieConsent(page)

        # Item rows — deliberate stable hook (verified on US cart).
        self._item_rows = page.locator('[data-test-locator="sectionTableRow"]')

        # Remove button — role+name via aria-label="Remove" primary.
        # data-test-locator="btnDelete" is the documented fallback.
        self._remove_buttons = page.get_by_role("button", name="Remove")

    # ---------------------------------------------------------------- navigation

    @allure.step("Open cart directly")
    def goto(self) -> None:
        """Navigate straight to the US cart URL (no region segment)."""
        url = f"{self._store_base_url}/cart"
        log.info("Navigating directly to %s", url)
        self.page.goto(url, wait_until="domcontentloaded", timeout=self._navigation_timeout)
        self.cookie_consent.dismiss_if_present()

    # ---------------------------------------------------------------- queries

    @allure.step("Count items in cart")
    def item_count(self) -> int:
        """Number of line-item rows currently in the cart.

        Synchronous against the current DOM. Callers that just mutated
        the cart should wait_for_item_count rather than read immediately.
        """
        return self._item_rows.count()

    @allure.step("Check cart contains product named: {name}")
    def contains_product(self, name: str) -> bool:
        """True if any row's text contains the product name.

        Verified: the row's innerText includes the product name
        (e.g. 'DJI FPV Remote Controller 3\\n\\nUSD $199...'). Matching
        by name (captured from the product page) keeps the assertion
        meaningful and the failure message legible.
        """
        rows = self._item_rows
        return any(name.lower() in rows.nth(i).inner_text().lower() for i in range(rows.count()))

    @allure.step("Check cart is empty")
    def is_empty(self) -> bool:
        return self._item_rows.count() == 0

    # ---------------------------------------------------------------- waits

    @allure.step("Wait for cart to contain {expected} item(s)")
    def wait_for_item_count(self, expected: int) -> None:
        """Wait until the row count settles to `expected`.

        Add lands here via navigation; remove is an in-page XHR that
        re-renders the list. Anchor on the observable row count, never
        a fixed delay (framework no-time.sleep rule).
        """
        log.info("Waiting for cart item count to reach %d", expected)
        self.page.wait_for_function(
            "(n) => document.querySelectorAll("
            "'[data-test-locator=\"sectionTableRow\"]').length === n",
            arg=expected,
            timeout=self._default_timeout,
        )

    # ---------------------------------------------------------------- actions

    @allure.step("Remove first item from cart")
    def remove_first_item(self) -> None:
        """Remove the first line item.

        Used as the tested user-flow step. After calling, wait via
        wait_for_item_count — removal is an async in-page update, not a
        navigation.
        """
        log.info("Removing first cart item")
        self.wait_for_visible(self._remove_buttons.first)
        self.click(self._remove_buttons.first)

    @allure.step("Remove all items from cart (teardown-safe)")
    def clear(self) -> None:
        """Empty the cart entirely. Safe on an already-empty cart.

        Used by the clean_cart fixture teardown as belt-and-braces.
        Removes one item at a time, waiting for the count to drop after
        each, because the list re-renders per removal (stale handles
        otherwise).
        """
        while self._item_rows.count() > 0:
            before = self._item_rows.count()
            self.click(self._remove_buttons.first)
            self.wait_for_item_count(before - 1)
        log.info("Cart cleared")

    def current_url(self) -> str:
        return self.page.url
