"""DJI marketing-site footer component.

Why a component, not a page: the footer appears at the bottom of every
page in the DJI marketing site (homepage, product pages, search results,
support pages, etc.). A test that needs to click a footer link on any
of those pages should not have to know which page it's on.

Recon notes (2026-05-28):
  * Footer is present in the initial DOM at first paint — no lazy load.
    51 visible links exist below the fold from the moment the page is
    parsed. We do not need to scroll to materialize them.
  * All current TC-NAV-004 DDT targets navigate same-tab (target='_self')
    and are unique by accessible name within <footer>.
  * The lower footer rows ("Who We Are", "Terms of Use") are plain inline
    <a> links (display:inline, ~16px tall). An explicit
    scroll_into_view_if_needed() on these proved flaky: while DJI's late
    analytics scripts (GTM, sentry, etc.) keep reflowing the page, the
    element's box never settles within the timeout and the standalone
    scroll call fails — even though the link is fully visible and unique.
    Playwright's click() does its own auto-scroll + stability wait and is
    more tolerant of this reflow churn, so we let click() own the scroll
    rather than calling scroll_into_view_if_needed() first. (This is why
    the higher footer links passed and the lower ones failed before.)
  * If a future target needs to open a new tab, swap expect_navigation
    for context.expect_page in a dedicated method — don't overload this
    one.
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
        page was still reflowing (see module docstring). wait_for_visible
        stays so that a genuinely missing link fails with a clean
        "not visible" message rather than an opaque click timeout.

        Same-tab navigation expected for all current DDT targets. If you
        add a target that opens a new tab, write a separate method.

        Args:
            name: Exact accessible name of the link, e.g. "Download Center",
                  "Terms of Use". Footer links take their name from visible
                  text (no aria-label), so what you see is what you pass.
        """
        link = self._footer.get_by_role("link", name=name, exact=True).first
        self.wait_for_visible(link)
        log.info("Clicking footer link: %s", name)
        with self.page.expect_navigation(
            wait_until="domcontentloaded",
            timeout=self._navigation_timeout,
        ):
            self.click(link)
