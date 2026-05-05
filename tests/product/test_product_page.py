"""Product detail page tests.

Two tests, two concerns:

  1. test_product_page_loads_directly — direct URL navigation. Verifies
     the product page renders with the expected title and Buy Now action.
     Fast and isolated. Doesn't depend on search.

  2. test_search_result_navigates_to_product_page — full UI journey from
     search → click first result → product page. Proves the navigation
     contract between SearchResultsPage and ProductPage works end to end.

We pick a flagship product (DJI Mavic 4 Pro) as the test target. If
DJI ever discontinues it, the test fails loudly and we update the slug.
That's a known maintenance cost of testing against a real, evolving
storefront — and a deliberate trade for not running our own staging.
"""

from __future__ import annotations

import allure
import pytest

from framework.pages.home_page import HomePage
from framework.pages.product_page import ProductPage
from framework.pages.search_results_page import SearchResultsPage

# Flagship product chosen as our stable target. Update if discontinued.
_TEST_PRODUCT_SLUG = "mavic-4-pro"
_TEST_PRODUCT_NAME = "DJI Mavic 4 Pro"


@pytest.mark.regression
@allure.title("Product page loads directly and renders expected elements")
@allure.description(
    "Navigate directly to /global/mavic-4-pro. Verify the product title in the "
    "sticky sub-nav matches and the Buy Now action is present."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_product_page_loads_directly(page) -> None:
    product = ProductPage(page)
    product.goto(_TEST_PRODUCT_SLUG)

    assert (
        _TEST_PRODUCT_SLUG in product.current_url()
    ), f"Expected URL to contain {_TEST_PRODUCT_SLUG!r}, got {product.current_url()!r}."
    assert (
        _TEST_PRODUCT_NAME in product.title()
    ), f"Expected title to contain {_TEST_PRODUCT_NAME!r}, got {product.title()!r}."
    assert (
        product.buy_now_is_visible()
    ), "Buy Now action not visible on product page. Check the trace."


@pytest.mark.regression
@allure.title("Search result click navigates to a product page")
@allure.description(
    "Full journey: open homepage → search 'mavic' → click first result → "
    "verify we land on a product page with a title and Buy Now action."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_search_result_navigates_to_product_page(page) -> None:
    home = HomePage(page)
    home.open()

    overlay = home.open_search_overlay()
    overlay.type_query("mavic")
    overlay.submit()

    results = SearchResultsPage(page)
    results.wait_for_results_settled()
    results.click_first_result()

    # We don't pin the exact slug — it depends on what DJI ranks first
    # for "mavic" today. We assert on the product-page contract instead.
    product = ProductPage(page)
    product.wait_for_visible(product._product_title)  # sticky nav title is our sentinel

    title = product.title()
    assert "DJI" in title, (
        f"Expected product title to contain 'DJI', got {title!r}. "
        f"URL is {product.current_url()!r}. Maybe a non-product page?"
    )
    assert (
        product.buy_now_is_visible()
    ), "Buy Now action not visible after navigating from search result."
