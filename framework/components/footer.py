"""DJI marketing-site footer component.

Why a component, not a page: the footer appears at the bottom of every
page in the DJI marketing site (homepage, product pages, search results,
support pages, etc.). A test that needs to click a footer link on any
of those pages should not have to know which page it's on.

Recon notes (2026-05-28):
  * Footer is present in the initial DOM at first paint — no lazy load.
    51 visible links exist below the fold from the moment the page is
    parsed. We do not need to scroll to materialize them.
  * Footer COLUMN HEADINGS are <p class="title"> elements (Product
    Categories, Service Plans, Where to Buy, Cooperation, Fly Safe,
    Support, Explore, Community, Subscribe). All ~24px tall and visible
    to Playwright. Used by TC-SMK-003.
  * All current TC-NAV-004 DDT targets navigate same-tab (target='_self')
    and are unique by accessible name within <footer>.
  * The lower footer rows ("Who We Are", "Terms of Use") are plain inline
    <a> links that Playwright treats as not-visible (clipped container);
    DDT targets avoid them. Click targets come from the upper column block.
  * click() does its own auto-scroll + stability wait; we do NOT call
    scroll_into_view_if_needed() (it was flaky during page reflow).
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from framework.config import ConfigReader
from framework.logger import get_logger
from framework.pages.base_page import BasePage

log = get_logger(__name__)


class Footer(BasePage):
    """DJI marketing-site footer. Construct from any page that renders it."""

    _navigation_timeout = ConfigReader.read_int("timeouts", "navigation_timeout_ms")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # <footer> is a single, stable landmark element. Scoping all
        # lookups here prevents false matches with same-named links in
        # other parts of the page.
        self._footer = page.locator("footer")

    @allure.step("Click footer link: {name}")
    def click_link(self, name: str) -> None:
        """Click a footer link by exact accessible name.

        We do NOT call scroll_into_view_if_needed() here. click() already
        auto-scrolls and waits for the element to be stable; the explicit
        scroll call was flaky on the lower inline footer links while the
        page was still reflowing. wait_for_visible stays so that a
        genuinely missing link fails with a clean "not visible" message
        rather than an opaque click timeout.

        Same-tab navigation expected for all current DDT targets. If you
        add a target that opens a new tab, write a separate method.

        Args:
            name: Exact accessible name of the link, e.g. "Download Center".
        """
        link = self._footer.get_by_role("link", name=name, exact=True).first
        self.wait_for_visible(link)
        log.info("Clicking footer link: %s", name)
        with self.page.expect_navigation(
            wait_until="domcontentloaded",
            timeout=self._navigation_timeout,
        ):
            self.click(link)

    @allure.step("Verify footer section heading is visible: {name}")
    def section_is_visible(self, name: str) -> bool:
        """True if a footer column heading with this exact text is visible.

        Footer column headings are <p class="title"> elements. We anchor
        on the text via get_by_text(exact=True) scoped to <footer>, so we
        don't match the build-hashed class and don't collide with links of
        a similar name elsewhere. Verified headings (recon 2026-05-28):
        Product Categories, Service Plans, Where to Buy, Cooperation,
        Fly Safe, Support, Explore, Community, Subscribe.

        Args:
            name: Exact heading text, e.g. "Product Categories".
        """
        heading = self._footer.get_by_text(name, exact=True).first
        return self.is_visible(heading)
