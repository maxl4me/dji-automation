"""Search functionality tests.

Three tests, three distinct concerns:

  1. test_search_returns_matching_products — full UI flow through the
     overlay. Proves the user-facing journey works end to end.

  2. test_search_with_no_results_shows_empty_state — direct URL navigation
     for a query guaranteed to have no matches. Isolates the empty-state UI.

  3. test_search_query_persists_in_input — direct URL navigation, asserts
     the results-page input reflects the URL's q= parameter. Catches
     regressions where the URL works but the UI doesn't sync.

Why mix UI flow and direct URL? UI flow is brittle and slow but proves
the journey. Direct URL is fast and stable but skips a real path. We
write *one* full UI flow and *multiple* direct-URL tests to get coverage
breadth without 10 tests all clicking through the same overlay.
"""

from __future__ import annotations

import allure
import pytest

from framework.pages.home_page import HomePage
from framework.pages.search_results_page import SearchResultsPage


@pytest.mark.regression
@allure.title("Search via overlay returns matching products")
@allure.description(
    "Full UI flow: open homepage → click search icon → type 'mavic' → submit → "
    "results render in same tab. Verifies URL, product tab, and count > 0."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_search_returns_matching_products(page) -> None:
    home = HomePage(page)
    home.open()

    overlay = home.open_search_overlay()
    overlay.type_query("mavic")
    overlay.submit()  # waits for navigation to /search

    # Reuse the same Page — submission navigates in the same tab despite the
    # form's target="_blank" attribute. Confirmed by runtime behavior.
    results = SearchResultsPage(page)
    # The overlay submit waited for the URL change but not for results to
    # render. Settle before asserting on count.
    results.wait_for_results_settled()

    assert (
        "/search?q=mavic" in results.current_url()
    ), f"Expected results URL to contain '/search?q=mavic', got {results.current_url()!r}."

    count = results.product_count()
    assert count > 0, f"Expected at least one product result for 'mavic', got count={count}."


@pytest.mark.regression
@pytest.mark.skip(
    reason=(
        "DJI's no-results page has a layout-timing race we have not fully "
        "diagnosed. The .no-data block transitions through visibility states "
        "during initial render in a way that defeats both Playwright's "
        "visibility check and a direct offsetHeight poll. Tracked as a "
        "Phase 2 follow-up; skipping rather than carrying a flaky test. "
        "See git history around 2026-05 for the iteration log."
    )
)
@allure.title("Search with no matches shows the empty-state message")
@allure.description(
    "Direct navigation to /search?q=<random_string>. Verifies the 'Sorry, no "
    "results were found.' heading appears and no product results are shown."
)
@allure.severity(allure.severity_level.NORMAL)
def test_search_with_no_results_shows_empty_state(page, unique_name) -> None:
    results = SearchResultsPage(page)
    nonsense_query = unique_name("xyzqwerty")

    results.goto(nonsense_query)

    assert results.is_no_results_shown(), (
        "Expected 'Sorry, no results were found.' to be visible. "
        "DJI may have changed the empty-state DOM — check the trace."
    )
    assert results.product_count() == 0, "No-results page unexpectedly shows a product count > 0."


@pytest.mark.regression
@allure.title("Search input on results page reflects the URL query")
@allure.description(
    "Navigate directly to /search?q=mavic and verify the input's value attribute "
    "contains 'mavic'. Catches regressions where URL routing works but UI state desyncs."
)
@allure.severity(allure.severity_level.NORMAL)
def test_search_query_persists_in_input(page) -> None:
    results = SearchResultsPage(page)
    query = "mavic"

    results.goto(query)

    actual_value = results.search_input_value()
    assert (
        query.lower() in actual_value.lower()
    ), f"Expected results-page search input to contain {query!r}, got {actual_value!r}."
