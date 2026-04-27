"""Phase 1 smoke test — proves the framework is wired up end-to-end.

What this test covers:
  * Browser launches, context opens, page navigates.
  * Playwright tracing is running.
  * Role-based locators resolve against the live DJI site.
  * Allure reporting attaches environment + (on failure) trace + screenshot.

What this test does NOT cover:
  * Any specific business flow. That starts in Phase 2.
"""

from __future__ import annotations

import allure
import pytest

from framework.config import ConfigReader
from framework.pages.home_page import HomePage


@pytest.mark.smoke
@allure.title("DJI Global homepage loads and renders the header")
@allure.description(
    "Navigates to the configured base URL, verifies the URL contains '/global', "
    "and confirms the <header> (role=banner) is visible."
)
@allure.severity(allure.severity_level.BLOCKER)
def test_homepage_loads(page) -> None:
    home = HomePage(page)

    home.open()

    expected_url_fragment = ConfigReader.read_str("app", "base_url")
    assert expected_url_fragment.rstrip("/") in home.current_url(), (
        f"Expected URL to contain {expected_url_fragment!r}, got {home.current_url()!r}. "
        "Possible geo-redirect; verify from the STD that /global is still the entry point."
    )

    assert home.header_is_visible(), (
        "Homepage header (role=banner) not visible within timeout. "
        "Check the Allure trace for the actual page state."
    )
