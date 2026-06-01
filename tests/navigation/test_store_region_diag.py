"""THROWAWAY CI diagnostic — DELETE after use.

Question: why does the CI runner land on store.dji.com/uk instead of the
US store? Two candidates:
  (1) DJI geo-routes the store by IP (the original "not IP-redirected"
      recon was done only from Israel and may have been the anomaly), or
  (2) a redirect chain sends every visitor to a regional store and the
      Israel result was the exception.

This runs ON THE RUNNER (push to a branch, let CI execute it) and prints
the ground truth: landing URL, redirect chain, region cookies, and the
runner's own IP-geolocation. Always passes; it only prints.

Run in CI by pushing this file on a branch and opening the run log.
Locally (from Israel) it prints the Israel-side view for comparison.
"""

from __future__ import annotations

import json
import urllib.request

from playwright.sync_api import sync_playwright


def test_store_region_diagnostic() -> None:
    # 1. What region does THIS machine's IP geolocate to?
    ip_info = {}
    try:
        with urllib.request.urlopen("https://ipinfo.io/json", timeout=10) as resp:
            ip_info = json.loads(resp.read().decode())
            # strip anything chatty; keep the region-relevant bits
            ip_info = {
                k: ip_info.get(k) for k in ("ip", "city", "region", "country", "org", "timezone")
            }
    except Exception as exc:
        ip_info = {"error": str(exc)}

    # 2. What does store.dji.com do on a fresh context?
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        redirects = []
        page.on(
            "response",
            lambda r: (
                redirects.append((r.status, r.url)) if r.request.is_navigation_request() else None
            ),
        )

        page.goto("https://store.dji.com", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)

        landing_url = page.url
        cookies = context.cookies()
        region_cookies = {
            c["name"]: c["value"]
            for c in cookies
            if c["name"].lower() in ("region", "ip_region", "country", "_dji_region")
        }
        # any cookie whose name hints at region, in case names differ
        region_like = {
            c["name"]: c["value"]
            for c in cookies
            if "region" in c["name"].lower() or "country" in c["name"].lower()
        }

        browser.close()

    out = {
        "runner_ip_geo": ip_info,
        "store_landing_url": landing_url,
        "navigation_responses": redirects[:12],
        "region_cookies_exact": region_cookies,
        "region_like_cookies": region_like,
    }

    print("\n\n===== STORE REGION DIAGNOSTIC (this environment) =====")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("===== END STORE REGION DIAGNOSTIC =====\n")
