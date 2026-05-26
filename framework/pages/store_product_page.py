"""DJI Store product detail page (store.dji.com/product/<slug>).

Distinct from the marketing-site ProductPage. The marketing product page
has a "Buy Now" link that funnels to the store; THIS page is the actual
transactional product page with a working "Add to Cart" button and a
post-add confirmation modal.

All selectors below were verified against the LIVE US-store DOM
(recon, 2026-05-19), not assumed:

  * URL shape: store.dji.com/product/<slug> — NO region segment. The
    /ca/product/... variant seen in early recon was the result of an
    explicit region click and must not be used. Verified on the US
    default store.

  * Add to Cart button:
      <button id="gtm_AddtoCart" class="...action-button-v2...">
        ... <p>Add to Cart</p>
    Primary: role=button + accessible name "Add to Cart" (Playwright
    derives the name from the nested <p>). Documented fallback hook:
    id="gtm_AddtoCart" — a GTM analytics id, business-stable.

  * Product title:
      <h1 class="style__product-title___ItCPV ...">DJI FPV ...</h1>
    Classes are build-hashed (volatile). Title is the page's primary
    <h1>; we anchor on the first h1. Rendered text == product name.

  * Confirmation modal (post-add):
      <main><h3>1 item(s) added to Cart</h3>
        <button>Continue Shopping</button>
        <a href="/cart"><button>View Cart & Check Out</button></a>
    Modal text lives in an <h3>; match substring "added to Cart".
    "View Cart & Check Out" is a <button> inside <a href="/cart"> —
    a genuine same-tab navigation, hence expect_navigation.

On owning the modal here (not as a component): it only appears as a
direct consequence of adding to cart on THIS page; it is not a reusable
cross-page fragment (unlike the cookie banner). A component for a
single-use modal would be premature abstraction.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from framework.components.cookie_consent import CookieConsent
from framework.config import ConfigReader
from framework.logger import get_logger
from framework.pages.base_page import BasePage

log = get_logger(__name__)


class StoreProductPage(BasePage):
    """A transactional product page on store.dji.com."""

    _store_base_url = ConfigReader.read_str("app", "store_base_url")
    _navigation_timeout = ConfigReader.read_int("timeouts", "navigation_timeout_ms")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.cookie_consent = CookieConsent(page)

        # Product title — page's primary <h1> (verified text == product
        # name). Classes are build-hashed, unusable.
        self._product_title = page.locator("h1").first

        # Add to Cart — role+name primary. id="gtm_AddtoCart" is the
        # documented fallback if the accessible name ever changes.
        self._add_to_cart_button = page.get_by_role("button", name="Add to Cart").first

        # Post-add modal: text is an <h3> "1 item(s) added to Cart".
        self._confirm_modal_text = page.get_by_text("added to Cart", exact=False)
        # "View Cart & Check Out": <button> inside <a href="/cart">.
        self._view_cart_button = page.get_by_role("button", name="View Cart & Check Out")

    @allure.step("Open product page directly: {slug}")
    def goto(self, slug: str) -> None:
        """Navigate directly to a US-store product page by slug.

        URL shape verified: no region prefix on the US default store.
        """
        url = f"{self._store_base_url}/product/{slug}"
        log.info("Navigating directly to %s", url)
        self.page.goto(url, wait_until="domcontentloaded", timeout=self._navigation_timeout)
        self.cookie_consent.dismiss_if_present()
        # Add to Cart visible == product is in stock and the page is
        # interactive. If the product is out of stock the store renders
        # "Notify Me" instead, this wait times out, and the failure
        # points at stock (see test docstring / STP risk row).
        self.wait_for_visible(self._add_to_cart_button)

    @allure.step("Read product title")
    def title(self) -> str:
        """Return the product name from the page's <h1>.

        Captured so the cart assertion can match by NAME rather than by
        slug or row position.
        """
        return self.inner_text(self._product_title).strip()

    @allure.step("Add product to cart")
    def add_to_cart(self) -> None:
        """Click Add to Cart and wait for the confirmation modal."""
        log.info("Clicking Add to Cart")
        self.click(self._add_to_cart_button)
        self.wait_for_visible(self._confirm_modal_text)

    @allure.step("Confirm add-to-cart modal is shown")
    def add_confirmation_is_visible(self) -> bool:
        return self.is_visible(self._confirm_modal_text)

    @allure.step("Go to cart via confirmation modal")
    def go_to_cart_via_modal(self) -> None:
        """Click 'View Cart & Check Out' (an <a href="/cart"> wrapping a
        <button>) — a genuine same-tab navigation. Caller asserts the
        destination (CartPage).
        """
        log.info("Navigating to cart via confirmation modal")
        with self.page.expect_navigation(
            wait_until="domcontentloaded",
            timeout=self._navigation_timeout,
        ):
            self.click(self._view_cart_button)

    def current_url(self) -> str:
        return self.page.url
