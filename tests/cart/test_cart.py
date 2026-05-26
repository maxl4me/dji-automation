"""Cart-as-guest tests (store.dji.com).

One test for this Phase 2 deliverable: the full add -> verify ->
remove -> verify-empty contract against the US store, as a guest.

All selectors used by the page objects below were verified against the
LIVE US-store DOM during recon (2026-05-19). See the individual page
objects' module docstrings for the confirmed DOM evidence.

Design decisions baked in (all evidence-backed):

  * US store is PINNED, not region-tolerant. Unlike the marketing site,
    the store is not IP-redirected: it defaults every visitor to the US
    store and records the real IP-region in a separate, unacted-upon
    cookie (region=US vs ip_region=IL, verified). US is therefore the
    deterministic default locally and in CI. assert_us_region() is a
    FAIL-LOUD guard, not a tolerant skip.

  * Cart isolation is provided by the existing per-test context fixture.
    The cart is keyed to a cart_uuid cookie; a fresh context has none,
    so the server issues a new one and the cart starts empty. The
    clean_cart fixture teardown is belt-and-braces (fires even on test
    failure), not load-bearing isolation.

  * Assert by product NAME, not slug or position. The name is captured
    from the product page <h1> and matched in the cart row's text
    (verified the name is present in row innerText).

  * Stop before payment (STD hard rule). Adds, verifies, removes.
    Never touches checkout, never enters payment data.

  * Known non-issue: the cart page logs a PayPal SDK console error
    ("zoid destroyed all components") from third-party-cookie/ad-block
    interference with PayPal's iframe. Unrelated to cart add/remove;
    the framework does not assert on console errors so it does not
    affect this test. Documented so a future console-error gate would
    not false-fail here.

Maintenance risk (tracked in STP): the pinned store product can go out
of stock. Symptom is product.goto() timing out on the Add to Cart wait
(the store renders "Notify Me" instead). That is NOT a cart regression
— update _PRODUCT_SLUG to a current in-stock item.
"""

from __future__ import annotations

import logging

import allure
import pytest

from framework.pages.cart_page import CartPage
from framework.pages.store_home_page import StoreHomePage
from framework.pages.store_product_page import StoreProductPage

# Pinned product. Chosen for: in stock at recon, an active product line
# (more evergreen than an accessory for an older device), plain
# "Add to Cart" with no forced variant/quantity picker. If discontinued
# or out of stock, the test fails loudly at product-page load — update
# this slug (see module docstring + STP risk row).
_PRODUCT_SLUG = "dji-fpv-remote-controller-3"


@pytest.fixture
def clean_cart(page):
    """Guarantee a clean cart around the test.

    Setup is a no-op for isolation (a fresh context already starts with
    an empty cart via a new cart_uuid cookie) but yields a CartPage for
    the test to reuse and for teardown.

    Teardown empties the cart regardless of test outcome. pytest runs
    fixture teardown after the yield even when the test fails, so an
    item added by a crashed test cannot survive into a rerun within the
    same context. Mirrors the conftest pattern of outcome-aware
    teardown. Teardown never raises — it must not mask the real failure.
    """
    cart = CartPage(page)
    yield cart
    try:
        cart.goto()
        cart.clear()
    except Exception as exc:
        logging.getLogger(__name__).warning("clean_cart teardown could not clear cart: %s", exc)


@pytest.mark.regression
@allure.title("Add a product to the cart and remove it (guest)")
@allure.description(
    "Full guest cart contract on the US store: open store -> assert US "
    "region (fail-loud guard) -> open product -> add to cart -> verify "
    "confirmation modal -> open cart -> verify product present by name "
    "-> remove -> verify cart empty. Stops before payment."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_add_and_remove_from_cart(page, clean_cart) -> None:
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
