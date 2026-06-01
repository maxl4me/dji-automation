# Software Test Plan (STP)

**Project:** DJI Global Storefront — UI Automation Framework
**Target Application:** https://www.dji.com/global and https://store.dji.com
**Author:** Max Rybkin
**Date:** 2026-05-31
**Version:** 0.4 (Draft)
**Status:** Block A complete (suite at 6 classes / 22 collected), CI green on main
**Companion documents:** [STD.md](STD.md) · [STD_Test_Scenarios.xlsx](STD_Test_Scenarios.xlsx) · [CI.md](CI.md)

---

## 1. Purpose and Audience

This Test Plan documents the operational view of the DJI automation suite: which tests exist, what they verify, how they run, what counts as a pass, and what the known issues are.

The Test Plan sits between two companion documents:
- The [Software Test Design (STD)](STD.md) answers *why* — scope, strategy, risks, stack.
- The [Test Scenario Catalogue (STD_Test_Scenarios.xlsx)](STD_Test_Scenarios.xlsx) is the design-level list of all ~30 scenarios (automated **and** designed-but-not-yet-automated), each with title, steps, and expected result.
- This Plan answers *what* and *when* for the **automated** subset — the specific tests, their execution, and their live status.

**Audience:**
- Engineers running or extending the suite
- Reviewers (course or portfolio) assessing test coverage
- Future-author returning to the project after a break

The test inventory in §6 is intentionally duplicated from the code-level Allure metadata. This is by design: a Test Plan is a human-readable artifact; pytest+Allure is the live source of truth. Both audiences exist.

## 2. Scope Reference

For full scope, in/out of scope items, environments, and assumptions, see [STD §3](STD.md#3-scope) through [§7](STD.md#7-environments). This Plan does not restate them.

In one sentence: the suite covers public, unauthenticated UI flows on `dji.com/global` (marketing site) and `store.dji.com` (transactional store) — homepage, navigation, search, product detail, store product detail, and guest cart — running headed Chromium locally and headless in CI, against production.

The two-site split matters and is reflected throughout this Plan:
- **Marketing site** (`dji.com/global`) is **IP-geo-redirected**; tests assert the *contract*, not the URL (region-tolerant).
- **Store** (`store.dji.com`) is **not** IP-redirected; it defaults every visitor to the US store. Store tests **pin** the US store as a deterministic default and assert it as a fail-loud guard.

## 3. Test Levels and Types

| Level / Type | Coverage |
|---|---|
| **End-to-end UI** | All current tests are UI-level acceptance tests in a real browser. |
| **Smoke** | Homepage reachability + key landmarks (nav, region indicator, footer). Runs first; failure here blocks subsequent test interpretation. |
| **Functional regression** | Navigation, search, product, store product, and cart flows. Marked `@pytest.mark.regression`. |
| **Negative tests** | Empty-query search (TC-SCH-005, passing) and no-results search (TC-SCH-002, skipped — see §9). |
| **DDT (data-driven)** | Footer links (TC-NAV-004) and multi-query search (TC-SCH-004); a third (store search, TC-STORE-003) is designed but not yet automated. |
| **API tests** | Out of scope for v1 (per STD §3.2). |
| **Visual / accessibility** | Out of scope. |

## 4. Test Environments

| Item | Value |
|---|---|
| Marketing URL | `https://www.dji.com/global` (Israel) / `https://www.dji.com/` (US, geo-redirected) |
| Store URL | `https://store.dji.com` (US default in every region; not IP-redirected) |
| Application environment | Production (no staging available; see STD §7) |
| Browser | Chromium (Playwright bundled) |
| OS for local execution | Ubuntu 24.04 LTS (developer machine) |
| OS for CI execution | Ubuntu 24.04 LTS (GitHub Actions, Azure West US runner) |
| Python | 3.11+ (3.12.3 local / 3.12 in CI) |
| Headless mode | Off locally (`headless = false`). Forced on in CI via `DJI_BROWSER__HEADLESS=true`. |
| Region | English routes only. DJI's geo-redirect means CI sees the US-regional marketing homepage; local runs from Israel see `/global`. The store is US-default everywhere. |

## 5. Test Data Strategy

| Concern | Approach |
|---|---|
| Account creation | Not used. All flows execute as guest. See STD §3.2. |
| Search queries | Deterministic for matching tests (`mavic`, plus `mini`/`osmo`/`ronin` in the DDT); empty string for the empty-query negative path; UUID-suffixed for the no-results path (`xyzqwerty-{uuid8}`) to prevent collisions. |
| Marketing product target | Hardcoded slug `mavic-4-pro` for the direct-load test (flagship, unlikely to be discontinued). |
| Store product target | Hardcoded slug `dji-fpv-remote-controller-3` for store price and cart tests (in stock at recon; one-line update if discontinued — see KI-003). |
| Cart isolation | The cart is keyed to a `cart_uuid` cookie. Each test runs in a fresh browser context, which has no `cart_uuid`, so the server issues a new one and the cart starts empty. Isolation is therefore free from the per-test context fixture; the `clean_cart` teardown is belt-and-braces, not load-bearing. |
| Cleanup | Tests do not modify persistent state (no accounts, no saved carts). |

## 6. Test Inventory

Each test below includes a stable test ID for cross-referencing, matching the IDs in [STD_Test_Scenarios.xlsx](STD_Test_Scenarios.xlsx). IDs are an STP-level convention, not enforced by code. Test files and the live Allure report are the canonical source.

Current totals: **6 test classes**, **16 scenario IDs**, **22 tests collected** (DDT cases expand to multiple runs). Local: 21 passed + 1 skipped. CI: 20 passed + 2 skipped (TC-PDP-001 additionally skips in CI per KI-002).

### 6.1 Smoke (`tests/smoke/`) — class `TestHomepageSmoke`

| Test ID | Title | Severity | Status | File |
|---|---|---|---|---|
| TC-SMK-001 | DJI homepage loads and renders the main navigation | Blocker | Passing | `tests/smoke/test_homepage_smoke.py` |
| TC-SMK-002 | Homepage shows the region indicator | Normal | Passing | `tests/smoke/test_homepage_smoke.py` |
| TC-SMK-003 | Homepage footer renders key column sections | Normal | Passing | `tests/smoke/test_homepage_smoke.py` |

**TC-SMK-001 — Homepage smoke**
- **Steps:** Navigate to `dji.com/global`. Verify URL is on a `dji.com` domain. Verify title contains "DJI". Verify the "Camera Drones" nav link is visible.
- **Expected:** All three assertions pass within the navigation timeout.
- **Notes:** URL assertion is region-tolerant (`dji.com`, not `/global`) because DJI redirects per request IP. The main-nav assertion is the strongest signal we're on a real DJI page regardless of region. Nav is located page-wide, not `<header>`-scoped (recon found no usable single `<header>` wrapping the nav).

**TC-SMK-002 — Region indicator present**
- **Steps:** Open homepage. Verify the region control is visible.
- **Expected:** The "Other Regions" region/language control is visible.
- **Notes:** Anchored on `div.language-box` (the visible container), **not** the "Other Regions" text span. In-Playwright recon proved the text span is inside a hidden flyout (`is_visible=False`) while the box is visible. `language-box` is a semantic class, not a build hash.

**TC-SMK-003 — Footer key sections present**
- **Steps:** Open homepage. Verify footer headings "Product Categories", "Support", "Explore" are visible.
- **Expected:** All three headings visible.
- **Notes:** A representative subset of the 9 footer column headings (recon-verified, all ~24px and visible). Asserting a subset keeps the test robust to minor column reorganisation.

### 6.2 Navigation (`tests/navigation/`) — class `TestMainNavigation`

| Test ID | Title | Severity | Status | File |
|---|---|---|---|---|
| TC-NAV-001 | Camera Drones nav navigates to camera-drones page | Normal | Passing | `tests/navigation/test_navigation.py` |
| TC-NAV-002 | Where to Buy nav navigates | Normal | Passing | `tests/navigation/test_navigation.py` |
| TC-NAV-003 | Support nav navigates | Normal | Passing | `tests/navigation/test_navigation.py` |
| TC-NAV-004 | Footer link navigates (DDT, 4 cases) | Normal | Passing | `tests/navigation/test_navigation.py` |

**TC-NAV-001 / 002 — Header product/retail nav**
- **Steps:** Open homepage. Click the named nav link. Read URL.
- **Expected:** URL contains `camera-drones` (001) / `where-to-buy` (002).
- **Notes:** Region-tolerant fragment assertions. Located page-wide by accessible name.

**TC-NAV-003 — Support nav (disambiguated)**
- **Steps:** Open homepage. Click the header "Support" link, pinned by its `from=nav` href fragment. Read URL.
- **Expected:** URL contains `/support`.
- **Notes:** "Support" matches more than one link on the homepage (header nav vs body); `href_contains` pins the header one.

**TC-NAV-004 — Footer link navigation (DDT)**
- **Steps:** Open homepage. Click footer link. Verify URL contains the expected fragment. Parametrized over 4 links.
- **Expected:** Download Center → `/downloads`; DJI Trust Center → `/trust-center`; Media Center → `/media-center`; Flagship Stores → `/where-to-buy/flagship`.
- **Notes:** All four targets are drawn from the footer's **upper column block** (verified visible to Playwright). The footer **bottom strip** (Who We Are, Terms of Use, etc.) is deliberately avoided — see KI-004.

### 6.3 Search (`tests/search/`) — class `TestSearch`

| Test ID | Title | Severity | Status | File |
|---|---|---|---|---|
| TC-SCH-001 | Search via overlay returns matching products | Critical | Passing | `tests/search/test_search.py` |
| TC-SCH-002 | Search with no matches shows the empty-state message | Normal | **Skipped** (KI-001) | `tests/search/test_search.py` |
| TC-SCH-003 | Search input on results page reflects the URL query | Normal | Passing | `tests/search/test_search.py` |
| TC-SCH-004 | Search returns products for multiple queries (DDT, 4 cases) | Normal | Passing | `tests/search/test_search.py` |
| TC-SCH-005 | Empty search query returns no products | Normal | Passing | `tests/search/test_search.py` |

**TC-SCH-001 — Overlay-driven search returns products**
- **Steps:** Open homepage. Open search overlay. Type `mavic`. Submit. Wait for results to settle.
- **Expected:** URL contains `/search?q=mavic`. Product count > 0.
- **Notes:** Submission is same-tab despite the form's `target="_blank"` markup (verified at runtime).

**TC-SCH-002 — No-results empty state** *(skipped — see §9 KI-001)*

**TC-SCH-003 — Query persists in input**
- **Steps:** Navigate `/search?q=mavic`. Read the results-page input value.
- **Expected:** Input value contains `mavic` (case-insensitive).
- **Notes:** Catches URL-routing-works-but-UI-desyncs regressions.

**TC-SCH-004 — Multi-query search (DDT)**
- **Steps:** Navigate `/search?q=<query>`. Verify URL reflects the query and count > 0. Parametrized over `mavic`, `mini`, `osmo`, `ronin`.
- **Expected:** Each query returns ≥ 1 product.
- **Notes:** Direct-URL navigation (fast, stable); the overlay path is exercised once by TC-SCH-001.

**TC-SCH-005 — Empty-query negative path**
- **Steps:** Navigate `/search?q=` (empty). Wait for settle. Read product count. Check no-data block.
- **Expected:** Product count = 0; no-data block visible.
- **Notes:** Recon (2026-05-31) showed the empty-query path renders a **stable, server-side** no-data state (`offsetHeight=108`, no product tab, zero product items). This is distinct from KI-001's random-query race — DJI short-circuits empty queries instead of running the search pipeline. See KI-001 for the implication.

### 6.4 Product Detail — marketing (`tests/product/`) — class `TestProductPage`

| Test ID | Title | Severity | Status | File |
|---|---|---|---|---|
| TC-PDP-001 | Product page loads directly and renders expected elements | Critical | Passing locally / **Skipped in CI** (KI-002) | `tests/product/test_product_page.py` |
| TC-PDP-002 | Search result click navigates to a product page | Critical | Passing (local + CI) | `tests/product/test_product_page.py` |

**TC-PDP-001 — Direct product page load**
- **Preconditions:** Execution from an Israel-region IP (see §9 KI-002).
- **Steps:** Navigate `/global/mavic-4-pro`. Read product title from the sticky sub-nav. Verify Buy Now action is visible.
- **Expected:** URL contains `mavic-4-pro`; title contains "DJI Mavic 4 Pro"; Buy Now visible.
- **Notes:** Skipped automatically when `CI=true`. If DJI discontinues the Mavic 4 Pro, this fails loudly locally — update `_TEST_PRODUCT_SLUG`.

**TC-PDP-002 — Search → product journey**
- **Steps:** Open homepage. Search `mavic`. Click the first result. Wait for the product sub-nav title.
- **Expected:** Product title contains "DJI"; Buy Now visible.
- **Notes:** Does not pin the destination slug — asserts the "click a result → land on a product page" contract, which holds in any region. Passes local + CI.

### 6.5 Product Detail — store (`tests/cart/`) — class `TestStoreProductPage`

| Test ID | Title | Severity | Status | File |
|---|---|---|---|---|
| TC-PDP-003 | Store product page renders a price | Normal | Passing (local + CI) | `tests/cart/test_cart.py` |

**TC-PDP-003 — Store product price renders**
- **Preconditions:** US store default; pinned product in stock.
- **Steps:** Open store home. Assert US region (fail-loud guard). Open the pinned product. Verify a price renders.
- **Expected:** A `USD $<amount>` price is visible.
- **Notes:** The **marketing** product page shows no price (Buy buttons only — verified by recon); pricing lives on `store.dji.com`, so this check belongs on the store. The price is anchored on the `USD $<digits>` **text pattern**, not the build-hashed price classes (`style__price___…`) which churn on every build. Lives in the cart test file because it shares the US-pinned store and the KI-003 stock dependency.

### 6.6 Cart — store (`tests/cart/`) — class `TestCart`

| Test ID | Title | Severity | Status | File |
|---|---|---|---|---|
| TC-CART-001 | Add a product to the cart and remove it (guest) | Critical | Passing (local + CI) | `tests/cart/test_cart.py` |

**TC-CART-001 — Guest add-and-remove**
- **Preconditions:** US store default; pinned product in stock.
- **Steps:** Open store; assert US region. Open product; add to cart; verify the confirmation modal. Open cart; verify the product is present by name. Remove the item; verify the cart is empty.
- **Expected:** Item appears in the cart, then the cart is empty after removal.
- **Notes:** Stops before payment (STD hard rule — no checkout, no card data). Verifies by product **name**, not slug or row position. KI-003 stock dependency applies. Cart isolation is free from the per-test context fixture.

## 7. Execution

### 7.1 Local execution

```bash
# Activate venv
source .venv/bin/activate

# Run the full suite
pytest

# Run by directory
pytest tests/smoke
pytest tests/navigation
pytest tests/search
pytest tests/product
pytest tests/cart

# Run by marker
pytest -m smoke
pytest -m regression

# Verbose output (recommended during development)
pytest -v

# Headless (faster, CI-style)
DJI_BROWSER__HEADLESS=true pytest
```

### 7.2 CI execution

Automatic on every push to `main` and on PRs targeting `main`. Also triggerable manually from the GitHub Actions tab.

```yaml
# Workflow: .github/workflows/tests.yml
# - Ubuntu 24.04 runner (Azure West US region)
# - Python 3.12
# - Chromium headless
# - Pip + Playwright browser caching
# - Allure results + traces uploaded as artifacts on every run
```

CI runtime: ~2 minutes cold (no cache), ~1 minute warm (caches hit). See [CI.md](CI.md) for the GitHub Actions / Jenkinsfile comparison.

### 7.3 Expected runtimes

Measured on a typical broadband connection, Chromium headed:

| Suite | Tests | Time (local) |
|---|---|---|
| Smoke only | 3 | ~10s |
| Navigation only | 7 (4 DDT cases) | ~60s |
| Search only | 8 (1 skipped, 4 DDT cases) | ~25s |
| Product only | 2 | ~10s |
| Cart only | 2 | ~20s |
| Full suite | 22 collected (1 skipped local) | ~120s |

Runtimes scale with network latency. Tests are not parallelized in v1 (Phase 5 deliverable).

### 7.4 Reporting

After any local run:
```bash
make allure-serve   # opens the report in a browser
```

After a CI run: download the `allure-results` artifact from the workflow run page, then `allure serve <path>`.

The report includes pass/fail/skip status with reasons, per-test step trace (Allure `@step`), and on failure: Playwright trace zip, screenshot, DOM snapshot, page URL, plus environment metadata.

## 8. Pass / Fail Criteria

### 8.1 Per-test
- A test passes when all of its assertions pass within the configured timeouts.
- A test fails if any assertion fails or any timeout fires.
- A test is skipped if marked with `@pytest.mark.skip` or `@pytest.mark.skipif` and a reason. Skips are not failures but require periodic review (§9).

### 8.2 Suite health (the stability bar)
- All non-skipped tests must pass three consecutive local runs against a stable network before the suite is considered "stable" for that build.
- A test that fails 1 in N runs (intermittent) is treated as a defect in the test, not a real regression, and is investigated before being treated as a failure indicator.
- Network or browser-process failures (`TargetClosedError`, transient timeouts after one bad first run) are tracked but do not invalidate the suite — see §10.

### 8.3 CI signal
- A green checkmark on `main` means the headless suite passed against DJI from a US-region runner. A red X must be investigated within the same day to avoid normalizing breakage on `main`.

## 9. Known Issues and Skipped Tests

| ID | Description | Status | Decision |
|---|---|---|---|
| KI-001 | TC-SCH-002 (no-results empty state) is skipped due to a timing race in DJI's no-results rendering for **random** queries. The `.no-data` block transitions through visibility states during initial render in a way that Playwright's locator visibility, raw `offsetHeight` polling, and a populated-count predicate all fail to handle reliably. | Open (re-investigable) | Skipped with documented reason. **Update 2026-05-31:** the *empty-query* path (TC-SCH-005) renders a **stable** server-side no-data state and passes reliably. This narrows KI-001 to the *random-string* path specifically — the race appears tied to the client-side search-and-fail pipeline, not the no-data block itself. Candidate for a fresh diagnostic in a later phase. |
| KI-002 | TC-PDP-001 (direct product page load) is skipped in CI because DJI's geo-redirect strips `/global` from non-Israel IPs and routes `/global/<slug>` back to the regional homepage. Direct product URL navigation requires an Israel-region IP. | Open | Skipped automatically where `CI=true`. TC-PDP-002 (search → product journey) covers the same surface area in any region and passes in both local and CI. |
| KI-003 | TC-CART-001 and TC-PDP-003 depend on a pinned store product (`dji-fpv-remote-controller-3`) being in stock. If out of stock, the store renders "Notify Me" instead of "Add to Cart"/price, and the relevant `goto()` wait times out. | Open | Fails loud with a documented symptom (not a silent skip). Fix is a one-line update to `_PRODUCT_SLUG`. Tracked as a maintenance risk, not a defect. |
| KI-004 | The DJI footer's **bottom strip** (Who We Are, Terms of Use, DJI Privacy Policy, etc.) renders inside a clipped container. The links report a box to `getBoundingClientRect` but Playwright's stricter visibility check treats them as not-visible, so `wait_for(state="visible")` and clicks time out. | Open (worked around) | TC-NAV-004's DDT targets are deliberately drawn from the footer's **upper column block** (Download Center, Trust Center, Media Center, Flagship Stores), which Playwright sees reliably. The bottom-strip links are knowingly not covered rather than carried as flaky. Documented here so it is a conscious omission, not an oversight. |

**Note — region indicator locator (TC-SMK-002):** recon's DOM dump showed an "Other Regions" text span that *appears* present, but an in-Playwright `is_visible()` probe proved it sits in a hidden flyout. TC-SMK-002 therefore anchors on the visible `div.language-box` container. General lesson recorded for the suite: a DOM dump reports what *exists*; only a Playwright visibility probe reports what the test will treat as *visible*. Vet text/CSS anchors with a `count()`+`is_visible()` probe before shipping.

Tracking principle: **a skipped (or knowingly uncovered) item with a written reason is preferable to a flaky test that erodes confidence in the entire suite.**

## 10. Risks and Mitigations (Operational)

For strategic risks see STD §8. This section covers operational risks for running and maintaining the suite.

| Risk | Mitigation |
|---|---|
| First-run browser-process flakiness on cold start (transient timeout, then cascade of `TargetClosedError`) | A single retry on cold-start failure is acceptable. Locally, rerun once before treating as a real failure. |
| Hardcoded marketing slug becoming invalid (Mavic 4 Pro discontinued) | TC-PDP-001 fails loudly with URL/title mismatch. Update `_TEST_PRODUCT_SLUG`. |
| Hardcoded store slug going out of stock (KI-003) | TC-CART-001 / TC-PDP-003 fail loudly at product-page load. Update `_PRODUCT_SLUG`. |
| DJI marketing/store redesign changing locators | Locator strategy prioritizes role/text/data-attributes over CSS classes; build-hashed classes are explicitly avoided (price uses a text pattern; region uses a semantic class). Fix in the page object only. |
| Geo-redirect serves different URLs by region | URL assertions are region-tolerant where possible; tests that genuinely require a specific region are skipped in CI with a documented reason (KI-002). |
| Footer bottom-strip not visible to Playwright (KI-004) | DDT targets the upper column block only. |
| Anti-bot detection blocking Playwright | Has not occurred to date. Keep parallelism low, no aggressive retry, no scraping patterns. |
| Loss of network mid-run | Tests fail; rerun on stable network. No test-level retry (deliberate — see STD §8). |

## 11. Roles and Responsibilities

| Role | Owner | Responsibilities |
|---|---|---|
| Test author | Max Rybkin | All test design, implementation, review, maintenance. |
| Test reviewer | Max Rybkin + AI mentor | Self-review enforced by pre-commit hooks (ruff, black) and STD/STP discipline. No human peer review. |
| Test executor | Max Rybkin (local) + GitHub Actions (CI) | Local headed, CI headless. |
| Defect triage | Max Rybkin | Failures investigated by reading failure logs, Playwright traces, and Allure reports. |

## 12. Schedule and Status

Per the STD's [Greenfield rollout plan](STD.md#10-deliverables):

| Phase | Deliverable | Status |
|---|---|---|
| 1 | Repo scaffold + first smoke test | Done |
| 2 | Page objects + core flow tests | **Done** — smoke, navigation, search, marketing product, store product, and guest cart all shipped across 6 classes. |
| 3 | Fixtures, config, logging, CI stub | **Done** — fixtures, config, logging done. GitHub Actions CI online and green. Jenkinsfile + CI.md added. |
| 4 | Expanded coverage | **Done** — suite at 22 collected tests, 6 classes, two DDTs. Test Scenario Catalogue (`STD_Test_Scenarios.xlsx`) documents the full design including ~14 designed-but-not-yet-automated scenarios. |
| 5 | Parallelization, full Jenkins pipeline | Pending. |

## 13. Glossary (for non-engineering reviewers)

- **Page Object Model (POM):** Architectural pattern where each page of the application has a corresponding Python class that owns its locators and actions. Tests interact with pages, not raw selectors.
- **Component:** A reusable UI fragment (e.g. the cookie-consent banner, the footer) modeled as its own class because it appears across multiple pages.
- **Locator:** A string or object that identifies a DOM element (e.g., `get_by_role("link", name="Buy Now")`).
- **DDT (Data-Driven Test):** One test body run against multiple data sets (e.g. the same search test for `mavic`, `mini`, `osmo`, `ronin`), implemented with `@pytest.mark.parametrize`.
- **Fixture:** A pytest mechanism for setting up and tearing down test resources (browser, context, page, test data).
- **Trace (Playwright):** A recorded timeline of every browser action during a test, replayable in a viewer for post-mortem debugging.
- **Allure:** A reporting tool that aggregates pytest results into a navigable HTML report with attachments.
- **Smoke test:** A fast, minimal test that verifies the system is reachable and basic wiring works.
- **Regression test:** A test that verifies a specific feature continues to work as expected.
- **CI (Continuous Integration):** A system that automatically runs the test suite on every code push, providing fast feedback on whether changes broke anything.

---

**Revision history**

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-05-05 | Initial draft. Reflects state at commit `03ed042` (5 passing, 1 skipped). |
| 0.2 | 2026-05-11 | Added CI execution section. Added KI-002 (geo-redirect skip for TC-PDP-001). Updated TC-SMK-001 description to reflect region-tolerant assertions. |
| 0.3 | 2026-05-19 | Added store coverage: `TestCart` (TC-CART-001) and store product page on `store.dji.com`. Added KI-003 (pinned store product stock dependency). Documented the marketing-vs-store environment split and US-store pinning. |
| 0.4 | 2026-05-31 | Added `TestMainNavigation` (TC-NAV-001/002/003/004 incl. footer DDT), TC-SMK-002/003 (region indicator, footer sections), TC-SCH-004 (multi-query DDT) and TC-SCH-005 (empty-query negative), and TC-PDP-003 (store price, `TestStoreProductPage`). Added KI-004 (footer bottom-strip not visible to Playwright) and the region-indicator locator note. Updated KI-001 with the empty-query-is-stable finding. Linked the new Test Scenario Catalogue (`STD_Test_Scenarios.xlsx`). Marked Phases 2–4 done. |
