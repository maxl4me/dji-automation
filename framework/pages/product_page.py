"""DJI product detail page — pages at /global/<product-slug> like /global/mavic-4-pro.

Why one page object for all products: DJI uses a shared template for
every product detail page. Same sub-nav, same Buy Now button placement,
same overall layout. One page object handles all of them, parameterized
by URL slug. Adding more product-specific assertions later doesn't change
that — they'd be additional methods on this same class.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from framework.config import ConfigReader
from framework.logger import get_logger
from framework.pages.base_page import BasePage

log = get_logger(__name__)


class ProductPage(BasePage):
    """Generic DJI product detail page (one class for all products)."""

    _base_url = ConfigReader.read_str("app", "base_url")
    _navigation_timeout = ConfigReader.read_int("timeouts", "navigation_timeout_ms")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Sub-nav title — sticky bar at the top of the page that shows the
        # product name. The class `product-subnav-title` is semantic (no
        # build hash) so we anchor on it.
        self._product_title = page.locator("div.product-subnav-title")

        # Buy Now action — sticky sub-nav has it as a link with accessible
        # name "Buy Now". Role+name is the most stable possible locator.
        self._buy_now = page.get_by_role("link", name="Buy Now").first

    # ---------------------------------------------------------------- navigation

    @allure.step("Open product page directly: {slug}")
    def goto(self, slug: str) -> None:
        """Navigate directly to a product page by URL slug.

        Args:
            slug: URL slug, e.g. 'mavic-4-pro'. We assemble the full URL
                  internally so callers don't think about the base.
        """
        url = f"{self._base_url}/{slug}"
        log.info("Navigating directly to %s", url)
        self.page.goto(url, wait_until="domcontentloaded", timeout=self._navigation_timeout)
        # The sub-nav title is a reliable "page rendered" sentinel.
        self.wait_for_visible(self._product_title)

    # ---------------------------------------------------------------- queries

    @allure.step("Read product title")
    def title(self) -> str:
        """Return the product name shown in the sticky sub-nav."""
        return self.inner_text(self._product_title).strip()

    @allure.step("Verify Buy Now action is present")
    def buy_now_is_visible(self) -> bool:
        return self.is_visible(self._buy_now)

    def current_url(self) -> str:
        return self.page.url
