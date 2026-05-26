"""Cookie consent banner component.

This is a *component* (not a page) because the privacy banner appears on
top of whatever store page you land on, rather than being a destination.
The STD anticipated this exact element (risk row: "Cookie/consent banner
changes — handle as a dedicated page component, assert dismissed before
each test"), so handling it as a reusable fragment is a planned decision,
not an afterthought.

Why it matters mechanically:
  The banner overlays the BOTTOM of the viewport. On the cart page that
  is exactly where the "Check Out" and "Continue Shopping" actions sit.
  An undismissed banner intercepts pointer events on anything beneath it,
  so clicks silently land on the banner instead of the intended control.
  Dismissing it before interacting is mandatory, not cosmetic.

Why "Reject All Cookies" and not "Accept":
  Rejecting keeps only essential cookies. We want the leanest, most
  deterministic state — fewer third-party trackers loading means fewer
  network races and console errors in traces. The cart's own cookies
  (region, cart_uuid) are essential and unaffected by this choice.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from framework.logger import get_logger
from framework.pages.base_page import BasePage

log = get_logger(__name__)


class CookieConsent(BasePage):
    """The 'We Value Your Privacy' banner on store.dji.com."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Role+name is our top-priority locator. The banner's buttons have
        # accessible names from their visible text. "Reject All Cookies"
        # is verbatim from recon (image 2/3, May 2026).
        self._reject_button = page.get_by_role("button", name="Reject All Cookies")

    @allure.step("Dismiss cookie consent banner if present")
    def dismiss_if_present(self) -> None:
        """Dismiss the banner if it is showing; no-op if it is not.

        The banner only appears once per cookie-scope (a fresh Playwright
        context shows it; a context that already dismissed it will not).
        Because each test gets a fresh context, it will normally be
        present — but we must not hard-fail if it is absent, since that
        would couple every store test to banner timing. Hence the
        soft `is_visible` check rather than `wait_for_visible`.
        """
        if self.is_visible(self._reject_button):
            log.info("Cookie consent banner present — dismissing (Reject All)")
            self.click(self._reject_button)
            # Wait for it to actually leave the DOM/viewport before
            # returning, so callers can immediately click underneath.
            self._reject_button.wait_for(state="hidden")
        else:
            log.info("Cookie consent banner not present — nothing to dismiss")
