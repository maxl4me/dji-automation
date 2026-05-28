"""Phase 1 smoke tests — prove the framework is wired up end-to-end and
the homepage's key landmarks render.

What these tests cover:
  * TC-SMK-001 — browser/context/page wiring, main nav renders.
  * TC-SMK-002 — region indicator ("Other Regions") renders.
  * TC-SMK-003 — footer key column headings render.

A note on region:
  DJI geo-redirects based on the request's IP. From Israel, /global stays
  as /global. From the US (e.g., GitHub Actions runners in Azure West US),
  DJI strips /global and serves the regional landing page from /. Both pages
  are valid DJI pages with the same nav, region switcher, and footer — only
  the URL differs. We assert the *contract*, not the URL. These pass in any
  region.
"""

from __future__ import annotations

import allure
import pytest

from framework.components.footer import Footer
from framework.pages.home_page import HomePage


@pytest.mark.smoke
class TestHomepageSmoke:
    """Smoke tests for the DJI Global homepage."""

    @allure.title("DJI homepage loads and renders the main navigation")
    @allure.description(
        "Navigates to the configured base URL, verifies we land on a DJI domain "
        "(any region), and confirms the main navigation is visible. Region-tolerant."
    )
    @allure.severity(allure.severity_level.BLOCKER)
    def test_homepage_loads(self, page) -> None:
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

    @allure.title("Homepage shows the region indicator")
    @allure.description(
        "Verifies the 'Other Regions' region/country switcher is visible on the "
        "homepage. A present region indicator is a signal the global chrome "
        "rendered correctly. Region-tolerant."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_region_indicator_present(self, page) -> None:
        home = HomePage(page)
        home.open()

        assert home.region_indicator_is_visible(), (
            "Region indicator ('Other Regions') not visible on the homepage. "
            "DJI may have changed the region-switcher markup — check the trace."
        )

    @allure.title("Homepage footer renders key column sections")
    @allure.description(
        "Verifies a representative set of footer column headings render: "
        "'Product Categories', 'Support', and 'Explore'. Confirms the footer "
        "structure is present without asserting on volatile link sets. "
        "Region-tolerant."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_footer_key_sections_present(self, page) -> None:
        home = HomePage(page)
        home.open()

        footer = Footer(page)

        # A representative subset, not all nine — these three span the
        # product, support, and content areas of the footer. Asserting a
        # subset keeps the test robust if DJI reorganizes minor columns.
        for section in ("Product Categories", "Support", "Explore"):
            assert footer.section_is_visible(section), (
                f"Footer section heading {section!r} not visible. DJI may have "
                "restructured the footer — check the trace."
            )
