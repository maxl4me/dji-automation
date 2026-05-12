"""Phase 1 smoke test — proves the framework is wired up end-to-end.

What this test covers:
  * Browser launches, context opens, page navigates.
  * Playwright tracing is running.
  * Role-based locators resolve against the live DJI site.
  * Allure reporting attaches environment + (on failure) trace + screenshot.

What this test does NOT cover:
  * Any specific business flow. That starts in Phase 2.

A note on region:
  DJI geo-redirects based on the request's IP. From Israel, /global stays
  as /global. From the US (e.g., GitHub Actions runners in Azure West US),
  DJI strips /global and serves the regional landing page from /. Both pages
  are valid DJI pages with the same nav and content — only the URL differs.

  We assert the *contract*, not the URL: "we're on a DJI page with the main
  navigation visible." This passes in any region.
"""

from __future__ import annotations

import allure
import pytest

from framework.pages.home_page import HomePage


@pytest.mark.smoke
@allure.title("DJI homepage loads and renders the main navigation")
@allure.description(
    "Navigates to the configured base URL, verifies we land on a DJI domain "
    "(any region), and confirms the main navigation is visible. Region-tolerant."
)
@allure.severity(allure.severity_level.BLOCKER)
def test_homepage_loads(page) -> None:
    home = HomePage(page)

    home.open()

    # Region-tolerant URL check: we just want to confirm we ended up on
    # a DJI domain. The exact path (/global vs /) varies by request IP.
    assert "dji.com" in home.current_url(), (
        f"Expected URL to contain 'dji.com', got {home.current_url()!r}. "
        "Page may have failed to load or been hijacked."
    )

    assert "DJI" in home.page_title(), (
        f"Page title does not contain 'DJI': got {home.page_title()!r}. "
        "Page may have rendered an error or anti-bot challenge instead. Check the trace."
    )

    # Strongest signal: the main product navigation rendered.
    # If this is visible, we're on a real DJI page regardless of URL.
    assert home.main_nav_is_visible(), (
        "Main navigation (Camera Drones link) not visible within timeout. "
        "Check the Allure trace for the actual page state."
    )
