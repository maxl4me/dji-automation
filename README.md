# DJI Storefront — UI Automation Framework

[![tests](https://github.com/maxl4me/dji-automation/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/maxl4me/dji-automation/actions/workflows/tests.yml)

A production-grade UI automation framework that exercises real user journeys across DJI's two public properties — the geo-redirected marketing site (`dji.com/global`) and the US-default online store (`store.dji.com`). Built solo as a learning and portfolio project, it pairs a Page Object Model test suite (Pytest + Playwright, Chromium) with full engineering documentation (test design, plan, and report) and green CI on every push. **22 tests across 6 classes**, two data-driven suites, Allure reporting, and a deliberate region-tolerance strategy that keeps the suite green from any country.

This project is as much about **engineering judgment** as code: every locator is chosen after live DOM recon, flaky behavior is documented and contained rather than papered over, and the *why* behind each decision is written down (see the docs below).

---

## Documentation

The test arc is documented end to end. Reviewers short on time: start with the STR (what happened) or the scenario catalogue (what's covered).

| Document | What it is |
|---|---|
| [`docs/STD.md`](docs/STD.md) | **Software Test Design** — scope, strategy, risk analysis, locator policy, stack rationale. Written before any code. |
| [`docs/STD_Test_Scenarios.xlsx`](docs/STD_Test_Scenarios.xlsx) | **Test Scenario Catalogue** — ~30 scenarios (title / steps / expected result), covering the automated suite plus designed-but-not-yet-automated flows. |
| [`docs/STP.md`](docs/STP.md) | **Software Test Plan** — the live test inventory, how it runs, pass/fail criteria, known issues. |
| [`docs/STR.md`](docs/STR.md) | **Software Test Report** — results of the latest full run (local + CI), defects, known issues, conclusions. |
| [`docs/CI.md`](docs/CI.md) | **CI documentation** — side-by-side of the GitHub Actions workflow and the portfolio Jenkinsfile. |

## What this demonstrates

- **Page Object Model done properly** — selectors live in page objects and components, never in tests; tests read as business intent (open → act → assert).
- **Data-driven testing** — parametrized suites for footer navigation and multi-query search (a third, store search, is designed in the catalogue).
- **Two sites, two strategies** — the marketing site is IP-geo-redirected, so its tests assert the *contract* (region-tolerant). The store also geo-routes by IP, so its tests *pin* the US store served to a local IP as a fail-loud guard and skip in CI (documented as a known issue).
- **Deterministic synchronization** — no `time.sleep`; waits anchor to navigation events, DOM predicates, and Playwright auto-wait. A custom settle predicate handles DJI's search-results render.
- **Flakiness contained, not hidden** — issues that can't be made reliable (a search render race, two geo-redirects, a clipped footer region) are documented as Known Issues with a deliberate skip-with-reason or fail-loud decision.
- **CI you can trust** — GitHub Actions runs the headless suite on every push; the runner result tracks local exactly apart from documented region skips.
- **Recon-first locators** — every new surface is inspected live (in-Playwright probes, not just DevTools) before a locator is written.

## Stack

- Python 3.12 (type hints, Google-style docstrings)
- Pytest (markers, fixtures, conftest layering)
- Playwright (sync API, Chromium)
- Allure reporting (screenshots, traces, logs on failure)
- GitHub Actions (CI, green on `main`) + a portfolio Jenkinsfile
- Ruff + Black + pre-commit; conventional commits

## Quick start (run from a fresh clone)

Prerequisites: Python 3.12+, and the Allure CLI to view reports
(`brew install allure` on macOS, `scoop install allure` on Windows, or see the
[Allure docs](https://allurereport.org/docs/install/) for Linux).

```bash
# 1. Clone
git clone https://github.com/maxl4me/dji-automation.git
cd dji-automation

# 2. Create and activate a venv
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# 3. Install the framework in editable mode with dev tools
make install
# or: pip install -e '.[dev]'

# 4. Install Playwright's Chromium browser binary
make browsers
# or: playwright install chromium

# 5. (optional) enable pre-commit hooks if you'll be committing
pre-commit install

# 6. Run the smoke tests
make smoke
# or: pytest -m smoke
```

Note on region: a few tests are pinned to a specific region and skip outside it
(see [Known issues in the STP](docs/STP.md#9-known-issues-and-skipped-tests)).
Run from an Israel IP to execute the full suite; from elsewhere those tests skip
cleanly and the rest run normally.

## Running tests

```bash
make test            # full suite
make smoke           # smoke tests only
pytest tests/search  # one suite
pytest -m regression # by marker
pytest -k footer     # tests matching a pattern
pytest -v            # verbose

# Headless (CI-style) without editing config:
DJI_BROWSER__HEADLESS=true pytest
```

Latest full run: **21 passed, 1 skipped** locally (~2m); **18 passed, 4 skipped**
in CI (the extra skips are region-dependent tests — see [`docs/STR.md`](docs/STR.md)).

## Running the tests in CI

CI runs automatically on every push to `main` and on PRs targeting `main`. You
can also trigger a run by hand — handy when DJI is transiently flaky and you want
to re-run without a no-op commit:

- **From the web:** repo → **Actions** tab → **tests** workflow → **Run workflow**
  → pick `main` → **Run workflow**.
- **From the CLI** (GitHub CLI):
  ```bash
  gh workflow run tests.yml --ref main
  gh run watch          # follow the run live
  gh run list --limit 1 # check the latest run's status
  ```

The workflow installs dependencies (pip + Playwright Chromium, both cached),
runs the suite headless, and uploads artifacts. A green check on `main` means the
headless suite passed from the runner.

## Viewing the Allure report from a CI run

CI uploads the raw Allure **results** (not a pre-built HTML report) as an artifact
on every run, pass or fail. To view the report:

1. Open the workflow run: repo → **Actions** → click the run you want.
2. Scroll to **Artifacts** and download **`allure-results`** (a zip). On a failed
   run you'll also see **`playwright-traces`**.
3. Unzip it, then generate and serve the report locally:
   ```bash
   unzip allure-results.zip -d allure-results
   allure serve allure-results
   ```
   `allure serve` builds the HTML report and opens it in your browser. The report
   includes pass/fail/skip status with reasons, per-step traces, and — on failures —
   the Playwright trace, a screenshot, the DOM snapshot, and the page URL.

To view a report from a **local** run instead, just run `make allure-serve` after
running the suite (results are written to `allure-results/` automatically).

## Configuration

Runtime config lives in `config.ini`. Environment variables prefixed with
`DJI_` override it, so CI runs headless without touching the file
(`DJI_BROWSER__HEADLESS=true`). The `__` separator maps to a section:
`DJI_BROWSER__HEADLESS` → `[browser] headless`.

## Project layout

```
dji-automation/
├── .github/workflows/tests.yml   # GitHub Actions CI
├── Jenkinsfile                   # Portfolio CI artifact (not deployed)
├── docs/                         # STD, STP, STR, CI, scenario catalogue
├── framework/                    # Importable package (pip install -e .)
│   ├── config.py                 # Typed, env-overridable config reader
│   ├── logger.py                 # Logger factory
│   ├── pages/                    # Page Objects — selectors live here
│   │   ├── base_page.py          # Generic helpers (no DJI logic)
│   │   ├── home_page.py          # Marketing homepage
│   │   ├── search_results_page.py
│   │   ├── product_page.py       # Marketing product page
│   │   ├── store_home_page.py    # store.dji.com homepage
│   │   ├── store_product_page.py # store.dji.com product page
│   │   └── cart_page.py          # store.dji.com cart
│   └── components/               # Reusable cross-page UI fragments
│       ├── search_overlay.py
│       └── cookie_consent.py
├── tests/
│   ├── conftest.py               # Fixtures (browser, context, page, tracing)
│   ├── smoke/                    # TestHomepageSmoke
│   ├── navigation/               # TestMainNavigation
│   ├── search/                   # TestSearch
│   ├── product/                  # TestProductPage
│   └── cart/                     # TestCart, TestStoreProductPage
├── config.ini · pyproject.toml · Makefile
└── .pre-commit-config.yaml · .gitignore
```

## Contributing to this repo (as the sole author)

- Feature branches off `main`, conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `ci:`).
- Pre-commit hooks enforce ruff + black; don't skip them.
- Every test must pass three consecutive local runs before being treated as stable.
