# Software Test Plan (STP)

**Project:** DJI Global Storefront — UI Automation Framework
**Target Application:** https://www.dji.com/global
**Author:** Max Rybkin
**Date:** 2026-05-11
**Version:** 0.2 (Draft)
**Status:** Phase 2 in progress, CI online
**Companion document:** [STD.md](STD.md)

---

## 1. Purpose and Audience

This Test Plan documents the operational view of the DJI automation suite: which tests exist, what they verify, how they run, what counts as a pass, and what the known issues are.

The Test Plan is companion to the [Software Test Design (STD)](STD.md). The STD answers *why* (scope, strategy, risks, stack); this Plan answers *what* and *when* (specific tests, execution, status).

**Audience:**
- Engineers running or extending the suite
- Reviewers (course or portfolio) assessing test coverage
- Future-author returning to the project after a break

The test inventory in §6 is intentionally duplicated from the code-level Allure metadata. This is by design: a Test Plan is a human-readable artifact; pytest+Allure is the live source of truth. Both audiences exist.

## 2. Scope Reference

For full scope, in/out of scope items, environments, and assumptions, see [STD §3](STD.md#3-scope) through [§7](STD.md#7-environments). This Plan does not restate them.

In one sentence: the suite covers public, unauthenticated UI flows on `dji.com/global` — homepage, search, product detail page — running headed Chromium against production.

## 3. Test Levels and Types

| Level / Type | Coverage |
|---|---|
| **End-to-end UI** | All current tests are UI-level acceptance tests in a real browser. |
| **Smoke** | One smoke test verifies the homepage renders and the framework wiring is sound. Runs first; failure here blocks subsequent test interpretation. |
| **Functional regression** | Search and product flows. Marked `@pytest.mark.regression`. |
| **Negative tests** | Currently one (no-results search) — skipped pending diagnostic. See §9. |
| **API tests** | Out of scope for v1 (per STD §3.2). |
| **Visual / accessibility** | Out of scope. |

## 4. Test Environments

| Item | Value |
|---|---|
| Application URL | `https://www.dji.com/global` (Israel) / `https://www.dji.com/` (US, geo-redirected) |
| Application environment | Production (no staging available; see STD §7) |
| Browser | Chromium (Playwright bundled) |
| OS for local execution | Ubuntu 24.04 LTS (developer machine) |
| OS for CI execution | Ubuntu 24.04 LTS (GitHub Actions, Azure West US runner) |
| Python | 3.11+ (3.12.3 local / 3.12.13 in CI) |
| Headless mode | Off locally (`headless = false`). Forced on in CI via `DJI_BROWSER__HEADLESS=true`. |
| Region | English routes only. DJI's geo-redirect means CI sees the US-regional homepage; local runs from Israel see `/global`. |

## 5. Test Data Strategy

| Concern | Approach |
|---|---|
| Account creation | Not used. All flows execute as guest. See STD §3.2. |
| Search queries | Deterministic for matching tests (`mavic`); UUID-suffixed for negative paths (`xyzqwerty-{uuid8}`) to prevent collisions. |
| Product target | Hardcoded slug `mavic-4-pro` for the direct-load test (chosen as a flagship unlikely to be discontinued). |
| Cleanup | Tests do not modify persistent state (no carts saved, no accounts touched). Each test runs in a fresh browser context for isolation. |

## 6. Test Inventory

Each test below includes a stable test ID for cross-referencing. IDs are not enforced by code; they are an STP-level convention. Test files and the live Allure report are the canonical source.

### 6.1 Smoke (`tests/smoke/`)

| Test ID | Title | Severity | Status | File |
|---|---|---|---|---|
| TC-SMK-001 | DJI homepage loads and renders the main navigation | Blocker | Passing | `tests/smoke/test_homepage_smoke.py` |

**TC-SMK-001 — Homepage smoke**
- **Preconditions:** Network reachable; Chromium installed; framework installed in editable mode.
- **Steps:** Navigate to `dji.com/global`. Verify URL is on a `dji.com` domain. Verify page title contains "DJI". Verify the "Camera Drones" nav link is visible.
- **Expected:** All three assertions pass within 15s navigation timeout.
- **Notes:** URL assertion is region-tolerant (`dji.com` rather than `/global`) because DJI redirects per request IP. The main-nav assertion is the strongest signal that we're on a real DJI page regardless of region.

### 6.2 Search (`tests/search/`)

| Test ID | Title | Severity | Status | File |
|---|---|---|---|---|
| TC-SCH-001 | Search via overlay returns matching products | Critical | Passing | `tests/search/test_search.py` |
| TC-SCH-002 | Search with no matches shows the empty-state message | Normal | **Skipped** (see §9) | `tests/search/test_search.py` |
| TC-SCH-003 | Search input on results page reflects the URL query | Normal | Passing | `tests/search/test_search.py` |

**TC-SCH-001 — Overlay-driven search returns products**
- **Preconditions:** Homepage loads.
- **Steps:** Open homepage. Click search trigger. Type `mavic`. Press Enter. Wait for results page to settle.
- **Expected:** URL contains `/search?q=mavic`. Product result count > 0.
- **Notes:** The form's `target="_blank"` markup does not apply for programmatic submissions; navigation is same-tab.

**TC-SCH-002 — No-results empty state** *(skipped — see §9 KI-001)*

**TC-SCH-003 — Query persists in input**
- **Preconditions:** None (direct URL navigation).
- **Steps:** Navigate to `/search?q=mavic`. Read the value of the search input on the results page.
- **Expected:** Input value contains `mavic` (case-insensitive).
- **Notes:** Catches regressions where URL routing succeeds but the UI state does not synchronize.

### 6.3 Product Detail (`tests/product/`)

| Test ID | Title | Severity | Status | File |
|---|---|---|---|---|
| TC-PDP-001 | Product page loads directly and renders expected elements | Critical | Passing locally / **Skipped in CI** (see §9 KI-002) | `tests/product/test_product_page.py` |
| TC-PDP-002 | Search result click navigates to a product page | Critical | Passing (local + CI) | `tests/product/test_product_page.py` |

**TC-PDP-001 — Direct product page load**
- **Preconditions:** Execution from Israel-region IP (see §9 KI-002).
- **Steps:** Navigate to `/global/mavic-4-pro`. Read product title from the sticky sub-nav. Verify Buy Now action is visible.
- **Expected:** URL contains `mavic-4-pro`. Title contains "DJI Mavic 4 Pro". Buy Now is visible.
- **Notes:** Skipped automatically in CI environments (when `CI=true` is set). If DJI discontinues the Mavic 4 Pro, this test will fail loudly locally; update `_TEST_PRODUCT_SLUG`.

**TC-PDP-002 — Search → product journey**
- **Preconditions:** Homepage loads; search returns ≥1 result for `mavic`.
- **Steps:** Open homepage. Search `mavic`. Click the first result. Wait for product page sub-nav title to render.
- **Expected:** Product title contains "DJI". Buy Now is visible.
- **Notes:** Test does not pin the destination slug — DJI's ranking for `mavic` may change *and* the destination URL pattern differs by region. The contract is "click a result → land on a product page," not "click → land on a specific product." This test passes from any region.

## 7. Execution

### 7.1 Local execution

```bash
# Activate venv
source .venv/bin/activate

# Run the full suite
pytest

# Run by directory
pytest tests/smoke
pytest tests/search
pytest tests/product

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

CI runtime: ~2 minutes cold (no cache), ~1 minute warm (caches hit).

### 7.3 Expected runtimes

Measured on a typical broadband connection, Chromium headed:

| Suite | Tests | Time (local) |
|---|---|---|
| Smoke only | 1 | ~5s |
| Search only | 3 (1 skipped) | ~12s |
| Product only | 2 | ~10s |
| Full suite | 6 (1 skipped) | ~20–30s |

Runtimes scale with network latency. A slow connection can extend full-suite time to 60s+. Tests are not parallelized in v1 (Phase 5 deliverable).

### 7.4 Reporting

After any local run:
```bash
make allure-serve   # opens the report in a browser
```

After a CI run: download the `allure-results` artifact from the workflow run page, then unzip and serve locally with `allure serve <path>`.

The report includes:
- Pass/fail/skip status with reasons
- Per-test step trace (Allure `@step` decorators)
- On failure: Playwright trace zip, screenshot, DOM snapshot, page URL
- Environment metadata (browser version, headless mode, Python version, base URL, timestamp)

## 8. Pass / Fail Criteria

### 8.1 Per-test
- A test passes when all of its assertions pass within the configured timeouts.
- A test is failed if any assertion fails or any timeout fires.
- A test is skipped if marked with `@pytest.mark.skip` or `@pytest.mark.skipif` and a reason. Skips are not failures but require periodic review (§9).

### 8.2 Suite health (the stability bar)
- All non-skipped tests must pass three consecutive local runs against a stable network before the suite is considered "stable" for that build.
- A test that fails 1 in N runs (intermittent) is treated as a defect in the test, not a real regression, and is investigated before being treated as a failure indicator.
- Network or browser-process failures (`TargetClosedError`, transient timeouts after one bad first run) are tracked but do not invalidate the suite — see §10 risks.

### 8.3 CI signal
- A green checkmark on `main` means the headless suite passed against DJI from a US-region runner. A red X must be investigated within the same day to avoid normalizing breakage on `main`.

## 9. Known Issues and Skipped Tests

| ID | Description | Status | Decision |
|---|---|---|---|
| KI-001 | TC-SCH-002 (no-results empty state) is skipped due to a timing race in DJI's no-results rendering. The `.no-data` block transitions through visibility states during initial render in a way that Playwright's locator visibility, raw `offsetHeight` polling, and a populated-count predicate all fail to handle reliably. | Open | Skipped with documented reason. Revisit with fresh diagnostic instrumentation in a future phase. |
| KI-002 | TC-PDP-001 (direct product page load) is skipped in CI because DJI's geo-redirect strips `/global` from non-Israel IPs and routes `/global/<slug>` back to the regional homepage. Direct product URL navigation requires an Israel-region IP. | Open | Skipped automatically in any environment where `CI=true`. TC-PDP-002 (search → product journey) covers the same surface area in any region and passes in both local and CI. |

Tracking principle: **a skipped test with a written reason is preferable to a flaky test that erodes confidence in the entire suite.**

## 10. Risks and Mitigations (Operational)

For strategic risks see STD §8. This section covers operational risks for running and maintaining the suite.

| Risk | Mitigation |
|---|---|
| First-run browser-process flakiness on cold start (transient timeout, then cascade of `TargetClosedError`) | A single retry on cold-start failure is acceptable. CI will configure `--reruns 1` on the first attempt; locally, rerun once before treating as a real failure. |
| Hardcoded product slug becoming invalid (Mavic 4 Pro discontinued) | TC-PDP-001 fails loudly with URL/title mismatch. Maintenance: update `_TEST_PRODUCT_SLUG` in `tests/product/test_product_page.py`. |
| DJI marketing redesign changing locators | Locator strategy prioritizes role/text/data-attributes over CSS classes. When breakage occurs, fix in the page object only — tests do not reference selectors directly. |
| Geo-redirect serves different URLs by region | URL assertions are region-tolerant where possible; tests that genuinely require a specific region are skipped in CI with a documented reason (see KI-002). |
| Anti-bot detection blocking Playwright | Has not occurred to date. Mitigation: keep parallelism low, no aggressive retry, no scraping patterns. |
| Loss of network mid-run | Tests fail; rerun on stable network. The framework does not retry at the test level (deliberate — see STD §8). |

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
| 2 | Page objects + core flow tests | In progress — search and product flows shipped. Cart-as-guest pending. |
| 3 | Fixtures, config, logging, CI stub | **Mostly done** — fixtures, config, logging done. GitHub Actions CI online. Jenkinsfile pending. |
| 4 | Expanded coverage | Pending |
| 5 | Parallelization, full Jenkins pipeline | Pending |

## 13. Glossary (for non-engineering reviewers)

- **Page Object Model (POM):** Architectural pattern where each page of the application has a corresponding Python class that owns its locators and actions. Tests interact with pages, not raw selectors.
- **Locator:** A string or object that identifies a DOM element (e.g., `get_by_role("link", name="Buy Now")`).
- **Fixture:** A pytest mechanism for setting up and tearing down test resources (browser, page, test data).
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
