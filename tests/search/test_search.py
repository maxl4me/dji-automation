"""Search functionality tests.

Tests:
  1. test_search_returns_matching_products — full UI flow through the
     overlay for 'mavic'. Proves the user-facing journey works end to end.
  2. test_search_with_no_results_shows_empty_state — SKIPPED (KI-001).
  3. test_search_query_persists_in_input — direct URL navigation, input
     reflects the URL's q= parameter.
  4. test_search_returns_products_for_queries — DDT across several product
     families (mavic/mini/osmo/ronin), each expected to return results.
  5. test_empty_search_returns_no_products — negative path. /search?q=
     renders the no-data block with zero products; we assert the contract
     ("no products for empty query") which holds regardless of UI changes.

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
class TestSearch:
    """Search overlay and search results page."""

    @allure.title("Search via overlay returns matching products")
    @allure.description(
        "Full UI flow: open homepage → click search icon → type 'mavic' → submit → "
        "results render in same tab. Verifies URL, product tab, and count > 0."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search_returns_matching_products(self, page) -> None:
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
    def test_search_with_no_results_shows_empty_state(self, page, unique_name) -> None:
        results = SearchResultsPage(page)
        nonsense_query = unique_name("xyzqwerty")

        results.goto(nonsense_query)

        assert results.is_no_results_shown(), (
            "Expected 'Sorry, no results were found.' to be visible. "
            "DJI may have changed the empty-state DOM — check the trace."
        )
        assert (
            results.product_count() == 0
        ), "No-results page unexpectedly shows a product count > 0."

    @allure.title("Search input on results page reflects the URL query")
    @allure.description(
        "Navigate directly to /search?q=mavic and verify the input's value attribute "
        "contains 'mavic'. Catches regressions where URL routing works but UI state desyncs."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_query_persists_in_input(self, page) -> None:
        results = SearchResultsPage(page)
        query = "mavic"

        results.goto(query)

        actual_value = results.search_input_value()
        assert (
            query.lower() in actual_value.lower()
        ), f"Expected results-page search input to contain {query!r}, got {actual_value!r}."

    @pytest.mark.parametrize(
        "query",
        ["mavic", "mini", "osmo", "ronin"],
        ids=["mavic", "mini", "osmo", "ronin"],
    )
    @allure.title("Search for '{query}' returns at least one product")
    @allure.description(
        "DDT across several DJI product families. Direct navigation to "
        "/search?q=<query>; verify the URL reflects the query and the product "
        "count is greater than zero. Uses direct URL (fast, stable) rather than "
        "the overlay; the overlay path is covered once by "
        "test_search_returns_matching_products."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_returns_products_for_queries(self, page, query: str) -> None:
        results = SearchResultsPage(page)

        results.goto(query)

        assert (
            query in results.current_url()
        ), f"Expected results URL to contain {query!r}, got {results.current_url()!r}."

        count = results.product_count()
        assert count > 0, f"Expected at least one product result for {query!r}, got count={count}."

    @allure.title("Empty search query returns no product results")
    @allure.description(
        "Negative path. Direct navigation to /search?q= (empty query). DJI's "
        "empty-query path renders a stable 'no-data' empty state (verified by "
        "in-Playwright recon 2026-05-31: no_data_offsetHeight=108, no product "
        "tab, no product items). The test asserts the contract — zero product "
        "results — which holds regardless of how DJI styles the empty UI. "
        "Note: the related KI-001 skipped test (random nonsense query) has a "
        "timing race; the empty-query path does NOT share that race because "
        "DJI short-circuits empty queries to a stable server-rendered state."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_empty_search_returns_no_products(self, page) -> None:
        results = SearchResultsPage(page)

        # SearchResultsPage.goto("") URL-encodes and calls
        # wait_for_results_settled, which resolves on the visible .no-data
        # block (verified). product_count()'s early-out branch returns 0 when
        # .no-data is present, so we don't need to handle a missing count span.
        results.goto("")

        count = results.product_count()
        assert count == 0, (
            f"Expected no product results for an empty query, got count={count}. "
            "DJI may have changed how empty queries are handled — check the trace."
        )
        assert results.is_no_results_shown(), (
            "Expected the empty-state ('no-data') block to be visible on an "
            "empty-query results page. DJI may have changed the empty-state DOM."
        )
