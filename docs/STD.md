# Software Test Design (STD)

**Project:** DJI Global Storefront — UI Automation Framework
**Target Application:** https://www.dji.com/global
**Author:** [Your Name]
**Date:** 2026-04-23
**Version:** 0.2 (Draft)
**Status:** Pre-implementation

---

## 1. Purpose

This document defines the testing strategy for a greenfield UI automation framework targeting the DJI Global public storefront. It establishes scope, approach, technology stack, risks, and acceptance criteria **before** any framework code is written, so that implementation choices are traceable to documented decisions rather than ad hoc.

Secondary purpose: serve as a portfolio artifact demonstrating that automation work was planned, not just coded.

## 2. Context and Constraints

- **Engagement type:** Self-directed learning and portfolio project. Not a paid engagement; no SLA, no stakeholders other than the author.
- **Team:** One QA engineer, no code reviewers, no dev support.
- **Target application:** Public marketing and e-commerce site, third-party-owned. We have no control over the application, no test environment, no test data, no APIs documented for our use.
- **Legal and ethical bounds:** Testing is read-only user simulation. No load testing, no scraping, no bypassing anti-bot protections, no real purchases, no real account creation where avoidable.

## 3. Scope

### 3.1 In Scope
- UI automation of public, unauthenticated user flows on `dji.com/global`.
- Functional checks against critical customer-facing paths: navigation, search, product discovery, product detail pages, cart operations **up to but not including payment submission**.
- Framework-level concerns: fixtures, config, logging, reporting, CI-readiness.
- API checks against public, unauthenticated endpoints **only when** they support a UI test (e.g., verifying a cart API response complements a cart UI assertion). API testing is not a standalone goal.

### 3.2 Out of Scope
- Mobile applications (iOS, Android) and mobile web viewport testing.
- Performance, load, and stress testing.
- Security testing (penetration, auth bypass, injection).
- Accessibility (WCAG) auditing — may be added later, not a v1 goal.
- Real payment flows. Tests stop at the pre-payment step; no card data is entered.
- Authenticated user flows. We do not create test accounts on a production site we do not own; this would violate DJI's terms of service regardless of intent. All flows execute as a guest user.
- Localization coverage beyond the English `global` region.
- Visual regression testing.
- Cross-browser execution (see §5).

### 3.3 Deferred (candidates for later phases)
- Firefox and WebKit execution.
- Mobile viewport emulation.
- Accessibility smoke checks via axe-core integration.
- API contract tests against public endpoints.

## 4. Test Approach

### 4.1 Methodology
- **Page Object Model (POM)** as the structural default. Selectors are encapsulated in page classes; tests express business intent only.
- **Risk-based test selection.** With a single engineer and no business owner, we cannot cover everything. Priority goes to flows that, if broken, would most damage a real user: homepage load, primary navigation, site search, product detail rendering, add-to-cart, cart review.
- **Black-box functional testing.** We have no source access; all validation is via observable UI and network behavior.
- **Deterministic synchronization.** No `time.sleep`. Waits are anchored to network responses (`expect_response`), DOM state (`wait_for`, `wait_for_function`), or Playwright's built-in auto-wait on locators. Flakiness is treated as a defect in the test, not the application.

### 4.2 Test Levels
Only one level applies: **end-to-end UI acceptance tests** simulating a real user in a real browser. No unit or integration levels for the application itself — we do not own it.

Framework code (utilities, helpers) is treated as trusted and not unit-tested at this stage. This is a deliberate scope cut for a solo project; if the framework grows complex, unit tests become worthwhile.

### 4.3 Test Types
- **Smoke tests:** fast checks that the site is reachable and the critical path renders. Run on every execution.
- **Functional tests:** business flow validation (search returns results, product page displays price, cart updates quantity).
- **Negative tests:** selective, where user error matters (empty search, invalid promo code). Not exhaustive.

### 4.4 Locator Strategy
Locators are chosen in this order of preference:
1. `get_by_role` with accessible name
2. `get_by_label`
3. `data-testid` attributes (if present — unlikely on a marketing site)
4. CSS selectors with stable classes or IDs
5. XPath (last resort, flagged in code review)

Marketing sites frequently ship hashed CSS class names from build tools. The framework must assume CSS classes are volatile and prefer role- and text-based locators.

## 5. Technology Stack and Environment

| Concern | Choice | Rationale |
|---|---|---|
| Language | Python 3.11+ | Author proficiency; strong Playwright support. |
| Test runner | Pytest | Fixture layering, plugin ecosystem, matches stack. |
| Browser automation | Playwright (sync API) | Built-in auto-wait, tracing, network interception. |
| Browser | Chromium | Covers majority user share; Playwright-native. |
| Reporting | Allure | Rich failure artifacts, trend history for CI. |
| CI | Jenkins (declarative pipeline) | Stack requirement. |
| VCS | Git, feature branches, conventional commits | Stack requirement. |
| Code quality | ruff, black, pre-commit | Enforced before commit. |
| Parallelization | pytest-xdist | Enabled from Phase 5. |
| Packaging | `pyproject.toml`, editable install | Makes imports unambiguous. |

**Chromium-only execution** is a deliberate trade-off. Rationale: a solo engineer multiplying browsers multiplies flakiness, CI time, and debugging surface. Chromium covers the majority of real-user traffic patterns. The framework is designed browser-agnostic (browser selection is a config value, locators avoid Chrome-only APIs) so Firefox and WebKit can be added later by config change, not rewrite.

Note: Playwright's "Chromium" is the open-source engine Chrome is built on. For functional testing the behavioral difference from Google Chrome is negligible. We will use the term *Chrome* informally and *Chromium* in code and config.

## 6. Test Data Strategy

- **No pre-existing test data** on the target site; it is a public production storefront.
- **Generated data:** unique identifiers (UUID suffixes) for any user input (search queries for negative paths, cart comments, etc.) to prevent collisions and aid traceability.
- **No persistent state:** tests assume a fresh browser context per test. No session reuse across tests in v1.
- **Cleanup:** tests must not leave residual state. Items added to cart are emptied in teardown where possible. Authenticated state is avoided entirely.

## 7. Environments

| Environment | URL | Purpose |
|---|---|---|
| Production | https://www.dji.com/global | Only target environment. |

There is no staging. Tests run against production. This constrains us: we cannot create destructive tests, cannot assume specific inventory, and must tolerate content changes without test failures on unrelated elements.

## 8. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Marketing DOM changes break locators | High | Medium | Role/label/text locators; avoid CSS class selectors; centralize in page objects. |
| Anti-bot detection blocks Playwright | Medium | High | Sane parallelism (≤2 workers initially); no scraping patterns; realistic user agent; back off if 403s appear. |
| Geo-redirects serve different content | Medium | Medium | Pin region to `/global` explicitly; assert URL after navigation. |
| Cookie/consent banner changes | High | Low | Handle consent banner as a dedicated page component; assert it is dismissed before each test. |
| Network flakiness (CDN, third-party scripts) | High | Medium | Network-anchored waits; Playwright traces on failure; reasonable retries at suite level, not test level. |
| Content inventory changes (products discontinued) | Medium | Medium | Use category-level selectors, not specific product names. Fail loudly if category empty. |
| Running against production | Certain | High | Hard rule: no checkout, no account creation, no destructive actions. Code review (self) flags any violation. |
| Temptation to use a shared test account for "convenience" | Medium | High | Explicitly out of scope (see §3.2). Isolation via fresh browser context + unique test data per test achieves the same goal without ToS risk. |
| Solo engineer, no code review | Certain | Medium | Pre-commit hooks enforce style; this STD plus STP act as a self-review checklist; tests must pass three consecutive runs before being marked stable. |

## 9. Entry and Exit Criteria

### 9.1 Entry Criteria (framework ready to begin writing tests)
- Repo scaffolded with folder structure per framework design rules.
- One passing smoke test against `dji.com/global` that loads the homepage and verifies a header element.
- Allure report generates locally with screenshots and Playwright trace on failure.
- `pyproject.toml`, ruff, black, pre-commit all operational.

### 9.2 Exit Criteria (framework considered v1-complete)
- Smoke, search, product detail, and cart flows covered by automated tests.
- Every test passes three consecutive local runs (flakiness gate).
- Jenkins pipeline executes suite and publishes Allure report.
- STP exists and is current.
- STR generated after a full run.

## 10. Deliverables

| Deliverable | Format | Phase |
|---|---|---|
| STD (this document) | Markdown | Pre-implementation |
| Repo skeleton + smoke test | Code | Phase 1 |
| Page objects + core flow tests | Code | Phase 2 |
| Fixtures, config, logging, CI stub | Code | Phase 3 |
| Expanded coverage (search, product, cart) | Code | Phase 4 |
| STP (Test Plan) | Markdown | Phase 4 start |
| Parallelization, full Jenkins pipeline | Code + config | Phase 5 |
| STR (Test Report) | Markdown | After first full CI run |

## 11. Assumptions

- `dji.com/global` remains reachable from the author's execution location (Tel Aviv, Israel) without a VPN. If geo-blocking occurs, scope revisits.
- The site does not actively block Playwright's Chromium user agent. If it does, the project pauses for a decision: change target site, or accept that some tests will fail for reasons outside test logic.
- The author has sole authority on scope changes. Any scope change updates this STD with a version bump.

## 12. Open Questions

- Will we need to handle a login flow at all for portfolio completeness? Currently out of scope; revisit if recruiters commonly ask for it.
- How are we handling secrets for Jenkins (if any credentials are ever needed)? Deferred until needed.

---

**Revision history**

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-04-23 | Initial draft. |
| 0.2 | 2026-04-23 | Clarified that no test accounts will be created; added risk row for shared-account temptation. |
