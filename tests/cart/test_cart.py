"""Store (store.dji.com) tests: guest cart flow and product-page checks.

Two classes, both against the US store as a guest:

  * TestCart — the full add -> verify -> remove -> verify-empty cart
    contract (TC-CART-001).
  * TestStoreProductPage — store product-page checks that aren't cart
    actions. Currently the price-renders check (TC-PDP-003).

Design decisions baked in (all evidence-backed):

  * US store is PINNED, not region-tolerant. Unlike the marketing site,
    the store is not IP-redirected: it defaults every visitor to the US
    store and records the real IP-region in a separate, unacted-upon
    cookie (region=US vs ip_region=IL, verified). US is therefore the
    deterministic default locally and in CI.

  * Cart isolation is provided by the existing per-test context fixture.
    The cart is keyed to a cart_uuid cookie; a fresh context has none,
    so the server issues a new one and the cart starts empty. The
    clean_cart fixture teardown is belt-and-braces, not load-bearing.

  * Stop before payment (STD hard rule). Adds, verifies, removes.
    Never touches checkout, never enters payment data.

  * Price is asserted by TEXT pattern ("USD $<digits>"), not by the
    build-hashed price classes, and not by slug/position. Verified by
    in-Playwright recon (2026-05-28): the pinned product renders
    "USD $199".

Maintenance risk (tracked in STP, KI-003): the pinned store product can
go out of stock. Symptom is goto() timing out on the Add to Cart wait
(the store renders "Notify Me" instead). That is NOT a regression —
update _PRODUCT_SLUG to a current in-stock item. Both classes share this
dependency because both load the same pinned product page.
"""

from __future__ import annotations

import logging

import allure
import pytest

from framework.pages.cart_page import CartPage
from framework.pages.store_home_page import StoreHomePage
from framework.pages.store_product_page import StoreProductPage

# Pinned product. Chosen for: in stock at recon, an active product line,
# plain "Add to Cart" with no forced variant/quantity picker. If
# discontinued or out of stock, tests fail loudly at product-page load —
# update this slug (see module docstring + STP KI-003).
_PRODUCT_SLUG = "dji-fpv-remote-controller-3"


@pytest.fixture
def clean_cart(page):
    """Guarantee a clean cart around the test.

    Setup is a no-op for isolation (a fresh context already starts with
    an empty cart via a new cart_uuid cookie) but yields a CartPage for
    the test to reuse and for teardown.

    Teardown empties the cart regardless of test outcome. Teardown never
    raises — it must not mask the real failure.
    """
    cart = CartPage(page)
    yield cart
    try:
        cart.goto()
        cart.clear()
    except Exception as exc:
        logging.getLogger(__name__).warning("clean_cart teardown could not clear cart: %s", exc)


@pytest.mark.regression
class TestCart:
    """Guest cart flows against store.dji.com."""

    @allure.title("Add a product to the cart and remove it (guest)")
    @allure.description(
        "Full guest cart contract on the US store: open store -> assert US "
        "region (fail-loud guard) -> open product -> add to cart -> verify "
        "confirmation modal -> open cart -> verify product present by name "
        "-> remove -> verify cart empty. Stops before payment."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_and_remove_from_cart(self, page, clean_cart) -> None:
        store = StoreHomePage(page)
        store.open()
        store.assert_us_region()  # fail-loud region guard

        product = StoreProductPage(page)
        product.goto(_PRODUCT_SLUG)
        product_name = product.title()
        assert product_name, "Product page rendered no title — check the trace."

        product.add_to_cart()
        assert product.add_confirmation_is_visible(), (
            "Add-to-cart confirmation modal did not appear. The add may have "
            "failed, or the modal markup changed. Check the Allure trace."
        )

        product.go_to_cart_via_modal()

        cart = clean_cart  # same CartPage instance used for teardown
        cart.wait_for_item_count(1)
        assert cart.contains_product(product_name), (
            f"Cart does not contain {product_name!r} after adding it. "
            f"Cart URL: {cart.current_url()!r}. Check the trace."
        )

        cart.remove_first_item()
        cart.wait_for_item_count(0)
        assert cart.is_empty(), (
            "Cart is not empty after removing the only item. Remove may have "
            "failed or the empty-state detection is wrong. Check the trace."
        )


@pytest.mark.regression
class TestStoreProductPage:
    """Store product-page checks that are not cart actions."""

    @allure.title("Store product page renders a price")
    @allure.description(
        "Open the pinned US-store product page and verify a 'USD $<amount>' "
        "price renders. The marketing product page shows no price (Buy buttons "
        "only); pricing lives on store.dji.com, so this check belongs here. "
        "Price is matched by text pattern, not by build-hashed CSS classes."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_store_product_price_renders(self, page) -> None:
        store = StoreHomePage(page)
        store.open()
        store.assert_us_region()  # fail-loud region guard

        product = StoreProductPage(page)
        product.goto(_PRODUCT_SLUG)

        assert product.price_is_visible(), (
            "No 'USD $<amount>' price visible on the store product page. "
            "Either the product is out of stock (see KI-003), or DJI changed "
            "the price markup. Check the trace."
        )
