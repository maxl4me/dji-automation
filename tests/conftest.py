"""Pytest fixtures for the DJI automation suite.

Key decisions:
  * One Playwright browser per session (expensive to launch).
  * One browser context per test (cheap, gives full isolation: cookies,
    storage, cache all start empty for each test).
  * Tracing is on by default (configurable); trace files are attached to
    Allure only on failure, then deleted. On success they are discarded.
  * Screenshots and DOM snapshots are ALSO attached on failure as a
    belt-and-braces aid, but the trace is the primary debugging artifact.
"""

from __future__ import annotations

import platform
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterator

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from framework.config import ConfigReader
from framework.logger import get_logger

log = get_logger(__name__)

_ALLURE_RESULTS = Path("allure-results")
_TRACE_DIR = Path("playwright-traces")
_ALLURE_ENV: dict[str, str] = {}


# --------------------------------------------------------------------- browser


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """Launch the browser once per test session.

    Chromium by default. Headless and slow-mo come from config.ini (env-overridable).
    """
    browser_type = ConfigReader.read_str("browser", "browser_type")
    headless = ConfigReader.read_bool("browser", "headless")
    slow_mo = ConfigReader.read_int("browser", "slow_mo_ms")

    if browser_type != "chromium":
        # Kept as a guardrail — the STD commits to Chromium-only in v1. Edit
        # config.ini only after a conscious decision to expand browser coverage.
        log.warning("browser_type=%s; STD commits to chromium in v1", browser_type)

    log.info("Launching %s (headless=%s, slow_mo=%dms)", browser_type, headless, slow_mo)
    with sync_playwright() as playwright:
        launcher = getattr(playwright, browser_type)
        instance = launcher.launch(headless=headless, slow_mo=slow_mo)

        _ALLURE_ENV["browser"] = browser_type
        _ALLURE_ENV["browser_version"] = instance.version

        yield instance
        instance.close()


# --------------------------------------------------------------------- context


@pytest.fixture
def context(browser: Browser, request: pytest.FixtureRequest) -> Iterator[BrowserContext]:
    """Fresh context per test. Tracing started/stopped here; retained on failure only."""
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="en-US",
    )

    tracing_enabled = ConfigReader.read_bool("tracing", "enabled")
    if tracing_enabled:
        ctx.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield ctx

    # Decide whether to keep the trace based on the test outcome.
    if tracing_enabled:
        if _test_failed(request.node):
            _TRACE_DIR.mkdir(parents=True, exist_ok=True)
            trace_path = _TRACE_DIR / f"{request.node.name}-{uuid.uuid4().hex[:6]}.zip"
            ctx.tracing.stop(path=str(trace_path))
            _attach_trace_to_allure(trace_path, request.node.name)
        else:
            # stop() with no path discards the trace (no disk write).
            ctx.tracing.stop()

    ctx.close()


# --------------------------------------------------------------------- page


@pytest.fixture
def page(context: BrowserContext, request: pytest.FixtureRequest) -> Iterator[Page]:
    """Fresh page per test. On failure, attach screenshot + URL + DOM to Allure."""
    page = context.new_page()
    page.set_default_timeout(ConfigReader.read_int("timeouts", "default_timeout_ms"))

    yield page

    if _test_failed(request.node) and not page.is_closed():
        _attach_failure_artifacts(page, request.node.name)

    page.close()


# --------------------------------------------------------------------- utility fixtures


@pytest.fixture
def unique_name() -> callable:
    """Factory for collision-free test data. UUID suffix so parallel runs don't clash."""

    def _make(prefix: str = "item") -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    return _make


# --------------------------------------------------------------------- pytest hooks


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    """Stash each phase's result on the item so fixtures can inspect it in teardown."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Write Allure environment.properties once the full suite has finished."""
    results_dir = Path(session.config.getoption("allure_report_dir") or _ALLURE_RESULTS)
    _write_allure_environment(results_dir)


# --------------------------------------------------------------------- helpers


def _test_failed(node: pytest.Item) -> bool:
    for phase in ("setup", "call", "teardown"):
        report = getattr(node, f"rep_{phase}", None)
        if report is not None and report.failed:
            return True
    return False


def _attach_trace_to_allure(trace_path: Path, test_name: str) -> None:
    try:
        allure.attach.file(
            str(trace_path),
            name=f"{test_name}-trace",
            extension="zip",
        )
    except Exception as exc:  # never break teardown on reporting issues
        log.warning("Failed to attach trace for %s: %s", test_name, exc)


def _attach_failure_artifacts(page: Page, test_name: str) -> None:
    """Best-effort failure artifacts. Each attachment is wrapped so one failure
    does not prevent the others from being captured."""
    try:
        allure.attach(
            page.screenshot(full_page=True),
            name=f"{test_name}-screenshot",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as exc:
        log.warning("screenshot failed: %s", exc)

    try:
        allure.attach(
            page.url or "about:blank",
            name=f"{test_name}-url",
            attachment_type=allure.attachment_type.TEXT,
        )
    except Exception as exc:
        log.warning("url capture failed: %s", exc)

    try:
        allure.attach(
            page.content(),
            name=f"{test_name}-dom",
            attachment_type=allure.attachment_type.HTML,
        )
    except Exception as exc:
        log.warning("DOM capture failed: %s", exc)


def _write_allure_environment(results_dir: Path) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    properties = {
        "browser": _ALLURE_ENV.get("browser", "chromium"),
        "browser_version": _ALLURE_ENV.get("browser_version", "unknown"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "headless": str(ConfigReader.read_bool("browser", "headless")),
        "base_url": ConfigReader.read_str("app", "base_url"),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    content = "\n".join(f"{k}={v}" for k, v in properties.items())
    (results_dir / "environment.properties").write_text(content, encoding="utf-8")
