"""Top navigation and footer link tests.

Coverage:
  * TC-NAV-001 — Camera Drones nav link → camera-drones page.
  * TC-NAV-002 — Where to Buy nav link  → where-to-buy page.
  * TC-NAV-003 — Support nav link       → support page.
  * TC-NAV-004 — Footer links (parametrized DDT, 4 cases) → expected pages.

Why region-tolerant URL assertions:
  DJI geo-redirects: from Israel the path stays /global/<x>, from US IPs
  /global is stripped and the path becomes /<x>. We assert on stable
  fragments (e.g. "camera-drones", "/trust-center") that appear in the
  URL in EITHER region. This is consistent with TC-SMK-001's contract-
  not-URL approach.

Why the DDT for footer but separate tests for header:
  The header tests each touch a different page area (product nav, retail
  nav, support nav) — they exercise different parts of the site. Different
  user journeys, different tests. Footer links are uniform: same component,
  same click, same assertion shape, only the data differs. Textbook DDT.

Why TC-NAV-003 passes href_contains:
  Recon shows "Support" matches TWO links on the homepage — the header nav
  link (href ...from=nav) and a body link (...from=homepage). We pin the
  header one by its href fragment. The other two nav names are unique.

Why these four footer targets specifically:
  Recon done IN THE TEST ENVIRONMENT (pytest -s dump, not a manual
  browser) showed the DJI footer has two structurally different regions:
    - An UPPER block of column links rendered as inline-block, ~24px tall,
      which Playwright reliably sees as visible.
    - A BOTTOM strip (Who We Are, Terms of Use, Privacy, etc.) rendered
      after a large hidden region-selector block (90+ display:none country
      links). Those bottom-strip links report a box to getBoundingClientRect
      but Playwright's stricter visibility check times out on them — they
      sit in an awkwardly-clipped container.
  Rather than fight the bottom strip, all four DDT targets are drawn from
  the proven-reliable upper block: same host (www.dji.com/global), all
  ~24px tall, all confirmed present and visible in the test's own region.
  This is the same "use what the test environment actually renders"
  discipline the nav tests follow.
"""

from __future__ import annotations

import allure
import pytest

from framework.components.footer import Footer
from framework.pages.home_page import HomePage


@pytest.mark.regression
class TestMainNavigation:
    """Header nav and footer link navigation from the homepage."""

    # ------------------------------------------------------------------ header

    @allure.title("Top nav: Camera Drones link navigates to camera-drones page")
    @allure.description(
        "Click the 'Camera Drones' link in the header. Verify the destination "
        "URL contains 'camera-drones'. Region-tolerant."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_nav_camera_drones(self, page) -> None:
        home = HomePage(page)
        home.open()

        home.click_nav_link("Camera Drones")

        assert (
            "camera-drones" in home.current_url()
        ), f"Expected URL to contain 'camera-drones', got {home.current_url()!r}."

    @allure.title("Top nav: Where to Buy link navigates to where-to-buy page")
    @allure.description(
        "Click the 'Where to Buy' link in the header. Verify the destination "
        "URL contains 'where-to-buy'. Region-tolerant."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_nav_where_to_buy(self, page) -> None:
        home = HomePage(page)
        home.open()

        home.click_nav_link("Where to Buy")

        assert (
            "where-to-buy" in home.current_url()
        ), f"Expected URL to contain 'where-to-buy', got {home.current_url()!r}."

    @allure.title("Top nav: Support link navigates to support page")
    @allure.description(
        "Click the 'Support' link in the header. Verify the destination URL "
        "contains '/support'. Region-tolerant. 'Support' is non-unique on the "
        "homepage, so we pin the nav link by its 'from=nav' href fragment."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_nav_support(self, page) -> None:
        home = HomePage(page)
        home.open()

        home.click_nav_link("Support", href_contains="support?site=brandsite&from=nav")

        assert (
            "/support" in home.current_url()
        ), f"Expected URL to contain '/support', got {home.current_url()!r}."

    # ------------------------------------------------------------------ footer (DDT)

    @pytest.mark.parametrize(
        ("link_name", "expected_path_fragment"),
        [
            ("Download Center", "/downloads"),
            ("DJI Trust Center", "/trust-center"),
            ("Media Center", "/media-center"),
            ("Flagship Stores", "/where-to-buy/flagship"),
        ],
        ids=["download-center", "trust-center", "media-center", "flagship-stores"],
    )
    @allure.title(
        "Footer link '{link_name}' navigates to a page containing '{expected_path_fragment}'"
    )
    @allure.description(
        "Open the homepage, click the named footer link, and verify the "
        "destination URL contains the expected path fragment. Parametrized "
        "across four links spanning different footer columns to exercise the "
        "Footer component, not just one column. Region-tolerant."
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_footer_link_navigates(
        self,
        page,
        link_name: str,
        expected_path_fragment: str,
    ) -> None:
        home = HomePage(page)
        home.open()

        footer = Footer(page)
        footer.click_link(link_name)

        assert expected_path_fragment in page.url, (
            f"Expected footer link {link_name!r} to land on a URL containing "
            f"{expected_path_fragment!r}, got {page.url!r}."
        )
