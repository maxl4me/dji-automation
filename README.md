# DJI Automation

[![tests](https://github.com/maxl4me/dji-automation/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/maxl4me/dji-automation/actions/workflows/tests.yml)

UI automation framework for the DJI Global storefront (`https://www.dji.com/global`).

Learning and portfolio project. See [`docs/STD.md`](docs/STD.md) for scope, strategy,
and rationale.

## Stack

- Python 3.11+
- Pytest
- Playwright (sync API, Chromium)
- Allure reporting
- Ruff + Black + pre-commit

## Quick start

Prerequisites: Python 3.11+, Allure CLI installed (`brew install allure` on macOS,
or see [Allure docs](https://allurereport.org/docs/install/)).

```bash
# 1. Create and activate a venv (in PyCharm: Project Interpreter -> Add)
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# 2. Install the framework in editable mode with dev tools
make install
# or: pip install -e '.[dev]'

# 3. Install Playwright's Chromium browser binary
make browsers
# or: playwright install chromium

# 4. Enable pre-commit hooks (one-time, per clone)
pre-commit install

# 5. Run the smoke test
make smoke
# or: pytest -m smoke

# 6. Open the Allure report
make allure-serve
```

## Running tests

```bash
make test          # full suite
make smoke         # smoke tests only
pytest -k homepage # tests matching a pattern
pytest -v          # verbose
```

## Configuration

Runtime config lives in `config.ini`. Environment variables prefixed with
`DJI_` override, so CI can run headless without editing the file:

```bash
DJI_BROWSER__HEADLESS=true pytest
```

## Project layout

```
framework/              # Importable package (pip install -e .)
  config.py             # Typed config reader
  logger.py             # Logger factory
  pages/                # Page Objects — selectors live here
    base_page.py        # Generic helpers (no DJI logic)
    home_page.py        # DJI homepage
  components/           # Reusable UI components (cookie banners, etc.)
tests/                  # Test suites
  conftest.py           # Fixtures (browser, context, page, tracing)
  smoke/                # Fast critical-path checks
docs/
  STD.md                # Software Test Design
scripts/                # Helper shell scripts
```

## Contributing to this repo (as the sole author)

- Feature branches off `main`, conventional commits (`feat:`, `fix:`, `chore:`).
- Pre-commit hooks enforce ruff + black; don't skip them.
- Every test must pass three consecutive local runs before being merged.
