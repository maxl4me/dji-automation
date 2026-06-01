# Software Test Report (STR)

**Project:** DJI Global Storefront — UI Automation Framework
**Target Application:** https://www.dji.com/global and https://store.dji.com
**Author:** Max Rybkin
**Date:** 2026-05-31
**Version:** 1.0
**Status:** Reporting the Block A end-of-phase run
**Companion documents:** [STD.md](STD.md) · [STD_Test_Scenarios.xlsx](STD_Test_Scenarios.xlsx) · [STP.md](STP.md) · [CI.md](CI.md)

---

## 1. Purpose

This Software Test Report records the outcome of executing the DJI automation suite at the end of Block A (suite buildout). It is the third document in the test arc:

- **STD** ([STD.md](STD.md)) — *why* we test: scope, strategy, risks, stack.
- **STP** ([STP.md](STP.md)) — *what* and *when*: the test inventory and how it runs.
- **STR** (this document) — *what happened*: results, defects, known issues, conclusions.

The figures below are from real executions on 2026-05-31, not estimates: a full local run and the corresponding CI run on `main`. Where the report references a test by ID (e.g. TC-CART-001), the IDs match the [STP inventory](STP.md#6-test-inventory) and the [scenario catalogue](STD_Test_Scenarios.xlsx).

## 2. Scope of This Report

This report covers the **automated** suite only — 6 test classes across smoke, navigation, search, marketing product, store product, and guest cart. The [scenario catalogue](STD_Test_Scenarios.xlsx) additionally documents ~14 designed-but-not-yet-automated scenarios; those are out of scope for an execution report (nothing ran) and are tracked for future phases.

Out of scope per [STD §3.2](STD.md#32-out-of-scope): mobile, performance, security, accessibility, real payment, authenticated flows, localization beyond English, visual regression, cross-browser.

## 3. Test Environment (as executed)

| Item | Local run | CI run |
|---|---|---|
| Date | 2026-05-31 | 2026-05-31 |
| Trigger | `pytest -v` (manual) | push of commit `d05240c` to `main` |
| OS | Ubuntu 24.04 LTS | Ubuntu 24.04 LTS (GitHub Actions, Azure West US) |
| Python | 3.12.3 | 3.12 |
| Browser | Chromium (Playwright bundled) | Chromium (Playwright bundled) |
| Headless | No (headed) | Yes (`DJI_BROWSER__HEADLESS=true`) |
| Region served | Israel — `dji.com/global` | US — `dji.com/` (geo-redirected); store US-default |
| Network | Residential broadband | Azure datacenter |

The region difference is the single most consequential environmental variable and is the cause of the one local-vs-CI result delta (see §5).

## 4. Execution Summary

### 4.1 Local run

```
collected 22 items
21 passed, 1 skipped in 130.91s (0:02:10)
```

| Outcome | Count |
|---|---|
| Passed | 21 |
| Skipped | 1 (TC-SCH-002 — KI-001) |
| Failed | 0 |
| Errors | 0 |
| **Total collected** | **22** |
| Wall-clock | 130.91s (~2m11s) |

"22 collected" counts the two DDTs by their parameter cases: TC-NAV-004 expands to 4 footer-link cases and TC-SCH-004 to 4 query cases. By distinct scenario ID the suite is 16 tests across 6 classes.

### 4.2 CI run

```
✓  docs(stp): expand STP to v0.4 ...   tests   main   push   26733388001   2m16s
```

| Outcome | Count |
|---|---|
| Passed | 20 |
| Skipped | 2 (TC-SCH-002 — KI-001; TC-PDP-001 — KI-002) |
| Failed | 0 |
| Wall-clock | 2m16s |

CI skips one test more than local: TC-PDP-001 is `skipif(CI=true)` because of the geo-redirect (KI-002). Everything else passes identically in both environments.

### 4.3 Results by class

| Class | Suite | Tests (collected) | Passed | Skipped (local / CI) |
|---|---|---|---|---|
| `TestHomepageSmoke` | smoke | 3 | 3 | 0 / 0 |
| `TestMainNavigation` | navigation | 4 IDs → 7 runs | 7 | 0 / 0 |
| `TestSearch` | search | 5 IDs → 8 runs | 7 | 1 / 1 |
| `TestProductPage` | product (marketing) | 2 | 2 local | 0 / 1 |
| `TestStoreProductPage` | store product | 1 | 1 | 0 / 0 |
| `TestCart` | cart (store) | 1 | 1 | 0 / 0 |

### 4.4 Per-test results (local run)

| Test ID | Test | Result |
|---|---|---|
| TC-SMK-001 | `test_homepage_loads` | Passed |
| TC-SMK-002 | `test_region_indicator_present` | Passed |
| TC-SMK-003 | `test_footer_key_sections_present` | Passed |
| TC-NAV-001 | `test_nav_camera_drones` | Passed |
| TC-NAV-002 | `test_nav_where_to_buy` | Passed |
| TC-NAV-003 | `test_nav_support` | Passed |
| TC-NAV-004 | `test_footer_link_navigates` ×4 (download-center, trust-center, media-center, flagship-stores) | Passed (4/4) |
| TC-SCH-001 | `test_search_returns_matching_products` | Passed |
| TC-SCH-002 | `test_search_with_no_results_shows_empty_state` | **Skipped (KI-001)** |
| TC-SCH-003 | `test_search_query_persists_in_input` | Passed |
| TC-SCH-004 | `test_search_returns_products_for_queries` ×4 (mavic, mini, osmo, ronin) | Passed (4/4) |
| TC-SCH-005 | `test_empty_search_returns_no_products` | Passed |
| TC-PDP-001 | `test_product_page_loads_directly` | Passed (local); skipped in CI (KI-002) |
| TC-PDP-002 | `test_search_result_navigates_to_product_page` | Passed |
| TC-PDP-003 | `test_store_product_price_renders` | Passed |
| TC-CART-001 | `test_add_and_remove_from_cart` | Passed |

## 5. Local vs CI Delta

There is exactly **one** difference between the two environments, and it is expected and documented:

| Test | Local | CI | Why |
|---|---|---|---|
| TC-PDP-001 (direct product load) | Passed | Skipped | DJI geo-redirects non-Israel IPs, stripping `/global/<slug>` back to the regional homepage. The CI runner is in Azure West US, so the direct product URL cannot resolve there. Skipped via `skipif(CI=true)` (KI-002). The same product surface is covered region-independently by TC-PDP-002, which passes in CI. |

No test produced a *different pass/fail verdict* between environments — the only delta is a deliberate, conditional skip. This is the intended design of the region-tolerance strategy ([STP §2](STP.md#2-scope-reference)).

## 6. Defects Found

**Zero application defects were raised against DJI.** This is expected and correct for this project: the target is a third-party production storefront we do not own, and the suite's purpose is to demonstrate framework engineering and exercise real flows, not to file bugs against DJI. Every assertion that could fail loudly (region pin, price presence, cart membership, nav destinations) passed.

The issues this project *did* surface are all **test-environment / target-behavior constraints**, not application defects — they are tracked as Known Issues (§7), the correct category for "the test cannot reliably run here" as opposed to "the application is broken."

## 7. Known Issues

Carried from [STP §9](STP.md#9-known-issues-and-skipped-tests). Status as of this report:

| ID | Summary | Effect on this run | Status |
|---|---|---|---|
| KI-001 | DJI's no-results page has a render timing race for **random** queries; the `.no-data` block's visibility cannot be made reliable. | TC-SCH-002 skipped (1 skip, both environments). | Open, re-investigable. The empty-query path (TC-SCH-005) was found to render a **stable** server-side no-data state and passes reliably, narrowing the race to the random-string/client-pipeline path specifically. |
| KI-002 | DJI geo-redirect strips `/global` from non-Israel IPs, so direct product-URL navigation only works from Israel. | TC-PDP-001 skipped in CI (the +1 CI skip). Passes locally. | Open. Same surface covered region-independently by TC-PDP-002. |
| KI-003 | The pinned store product (`dji-fpv-remote-controller-3`) must be in stock for the store price and cart tests. | No effect this run — product was in stock; TC-PDP-003 and TC-CART-001 both passed. | Open (maintenance risk). Fails loud with a documented symptom if OOS; one-line slug fix. |
| KI-004 | The marketing footer's bottom-strip links render in a clipped container Playwright treats as not-visible. | No effect on results — TC-NAV-004 deliberately targets the upper-column footer links, all of which passed. | Open (worked around). Bottom-strip links knowingly not covered. |

## 8. Stability Assessment

The suite is held to a three-consecutive-pass flakiness gate ([STP §8.2](STP.md#82-suite-health-the-stability-bar)) before any test is treated as stable. Observations supporting stability at this report:

- **No failures** in either the local or CI run.
- **No intermittent (1-in-N) failures** observed across the runs leading up to this report; the green CI history on `main` spans the full Block A buildout.
- **Synchronization is deterministic** — no `time.sleep`; waits are anchored to navigation events, DOM predicates, and Playwright auto-wait. The search results page uses an explicit settle predicate (populated count OR no-data block) rather than a blind wait.
- **The one skip is intentional and stable** — TC-SCH-002 is skipped by decision, not flaking; it does not enter the gate.

The known cold-start risk (first-run browser-process flakiness, then `TargetClosedError` cascade) did not occur in this run. Per policy it would warrant a single rerun, not a failure verdict.

## 9. Coverage Achieved

Against the [STD scope](STD.md#3-scope) and the critical-path priorities defined there:

| Critical path (STD §4.1) | Covered by | Status |
|---|---|---|
| Homepage load | TC-SMK-001 | ✅ |
| Primary navigation | TC-NAV-001/002/003, TC-SMK-003 | ✅ |
| Site search | TC-SCH-001/003/004/005 | ✅ (no-results path skipped, KI-001) |
| Product detail rendering | TC-PDP-001/002 (marketing), TC-PDP-003 (store price) | ✅ |
| Add-to-cart / cart review | TC-CART-001 | ✅ |
| Region behavior (marketing geo-redirect; store US-pin) | TC-SMK-002 + region-tolerant assertions throughout; store US-pin guard | ✅ |

All critical customer-facing paths identified in the STD are exercised by at least one automated test. The negative-path surface is partially covered (empty-query yes; no-results skipped pending KI-001 diagnosis).

## 10. Conclusions

- **The suite is green and stable.** 21/21 non-skipped tests pass locally; 20/20 pass in CI; zero failures; one intentional skip locally, two in CI (both documented).
- **All critical paths from the STD are covered.** The framework exercises real flows across two distinct DJI properties (geo-redirected marketing site and US-pinned store) with region-appropriate strategies for each.
- **No application defects** were found — appropriate for a portfolio framework against a production third-party site.
- **The four known issues are understood and contained.** None reflects a framework defect; each is a documented target-behavior or environment constraint with a deliberate handling decision (skip-with-reason or fail-loud), in line with the project principle that a documented skip beats a flaky test.
- **CI provides a trustworthy signal.** The headless US-runner result tracks the local result exactly apart from the one documented region skip, which validates the region-tolerance design.

## 11. Recommendations / Next Steps

In priority order, carried into the remaining phases:

1. **Re-investigate KI-001.** The empty-query path's stability (TC-SCH-005) is new evidence that the no-data block itself is sound; the race is likely in the random-query client pipeline. A fresh diagnostic with in-Playwright instrumentation may let TC-SCH-002 be un-skipped.
2. **Automate the designed scenarios.** ~14 scenarios in the catalogue are designed but not yet automated (Session 3 cart/store variations, a newsletter form-fill, the region flyout). These extend coverage breadth without new architecture.
3. **Phase 5 deliverables.** Parallelization (`pytest-xdist`) and the full Jenkins pipeline remain pending per the STD rollout plan.
4. **Periodic KI review.** KI-003 (stock dependency) in particular needs a glance before each reporting run, since it depends on live inventory.

---

**Revision history**

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-05-31 | Initial report. Covers the Block A end-of-phase run: local 21 passed / 1 skipped (130.91s) and CI 20 passed / 2 skipped on commit `d05240c`. Zero failures, zero application defects. KI-001/002/003/004 reported. |
