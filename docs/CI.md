# Continuous Integration

**Project:** DJI Global Storefront — UI Automation Framework
**Audience:** Engineers extending the suite; reviewers evaluating the project.

This document explains the project's CI setup. Two pipelines exist; only
one of them actually runs.

## Summary

| Pipeline | File | Status | Trigger |
|---|---|---|---|
| GitHub Actions | `.github/workflows/tests.yml` | **Live** — runs on every push to `main`, every PR, manual dispatch. | Push, pull request, manual |
| Jenkins | `Jenkinsfile` | **Static** — committed as a portfolio artifact. Not deployed to a running Jenkins instance. | SCM poll every 5 min, manual ("Build Now") |

The GitHub Actions pipeline is the project's real CI. The Jenkinsfile is
included because Jenkins is the dominant CI in enterprise QA shops and a
working pipeline file demonstrates the skill more concretely than a
résumé bullet. Setting up and operating a real Jenkins instance for a
solo portfolio project would add cost and maintenance for no signal gain.

## Why two pipelines?

This is an honest answer, not a hand-wave.

**GitHub Actions is the right choice for this project.** It's free for
public repos, lives next to the code, runs on every push without setup,
and reports status in pull requests automatically. There's no
infrastructure to maintain. For a one-engineer learning project on a
public GitHub repo, anything else would be overengineering.

**Jenkins is the right choice for many companies.** It runs on hardware
the company controls, integrates with on-prem secrets management, and
supports complex multi-pipeline topologies (matrix builds, distributed
agents, shared libraries) that GitHub Actions handles less ergonomically.
QA roles in finance, defense, and large enterprises routinely list
Jenkins as a required skill.

Carrying both files gives reviewers two signals:

1. The actual test suite is green in CI (GitHub Actions badge / Actions
   tab on the repo).
2. The author can write a Jenkins pipeline that does the same thing.

## What both pipelines do

| Step | GitHub Actions | Jenkins |
|---|---|---|
| Check out source | `actions/checkout@v4` | Implicit (declarative pipeline) |
| Provide Python 3.12 | `actions/setup-python@v5` | `python:3.12` via Playwright Docker image |
| Install framework | `pip install -e '.[dev]'` | `pip install -e '.[dev]'` |
| Install Chromium | `playwright install chromium` + `install-deps` | Preinstalled in `mcr.microsoft.com/playwright/python` image |
| Force headless mode | `env: DJI_BROWSER__HEADLESS=true` | `environment { DJI_BROWSER__HEADLESS = 'true' }` |
| Run suite | `pytest -v` | `pytest -v` |
| Archive Allure results | `upload-artifact` with `if: always()` | `archiveArtifacts` in `post { always { ... } }` |
| Archive Playwright traces | `upload-artifact` with `if: failure()` | `archiveArtifacts` in `post { failure { ... } }` |
| Build timeout | `timeout-minutes: 15` | `timeout(time: 15, unit: 'MINUTES')` |

The same env-var override mechanism (`DJI_BROWSER__HEADLESS=true`) works
in both pipelines because the framework's config reader is environment-
aware — see [framework/config.py](../framework/config.py). `config.ini`
stays unchanged for local development.

## Differences worth knowing

### Caching

GitHub Actions caches pip and the Playwright browser binary explicitly
via `actions/cache@v4`, keyed on `pyproject.toml` hash. Cold start ≈ 2
minutes; warm cache ≈ 1 minute.

The Jenkinsfile uses a Docker agent (`mcr.microsoft.com/playwright/python`).
The image ships with Chromium preinstalled, so no browser-install step is
needed. Pip dependencies are reinstalled every build inside the
container — Jenkins agents are stateful between builds, but Docker
agents reset between builds by design. This is an accepted trade-off:
slower than a cached pip install, but every build runs in an identical
clean environment.

### Triggers

GitHub Actions runs on `push`, `pull_request`, and manual `workflow_dispatch`.
This is event-driven — GitHub pushes the event to Actions immediately.

Jenkins uses SCM polling (`pollSCM('H/5 * * * *')`) — Jenkins asks GitHub
every 5 minutes whether anything new is on `main`. This is pull-based
and adds up to 5 minutes of latency before a build kicks off. The
production-grade alternative is a GitHub webhook from GitHub → Jenkins,
which is event-driven and instant. Polling is shown here because it
works without configuring Jenkins to be reachable from GitHub, which a
reviewer can verify by reading the file alone.

### Failure artifacts

Both pipelines attach Playwright traces only when the build fails.
GitHub Actions has a 14-day retention configured explicitly. Jenkins
inherits the global `buildDiscarder` policy declared in the pipeline
(`numToKeepStr: '20'`), which keeps artifacts for the last 20 builds
regardless of age.

## How to read the artifacts

### GitHub Actions

1. Go to the **Actions** tab on the repo.
2. Click the run you care about.
3. Scroll to the **Artifacts** section at the bottom.
4. Download `allure-results.zip` (every run) or `playwright-traces.zip`
   (only when a build failed).
5. Unzip locally and serve the Allure report:

```bash
allure serve <path/to/allure-results>
```

### Jenkins (hypothetical)

1. Open the build's page in the Jenkins UI.
2. Click **Build Artifacts** in the left nav.
3. Download `allure-results/` (every build) or `playwright-traces/`
   (only failed builds).
4. Same `allure serve` command locally.

## When to update which file

Both files describe the same pipeline. If you change the test command,
the timeout, the headless mechanism, or any of the artifact rules,
update **both files in the same commit** so they don't drift. The
comparison table in this document is the easiest way to verify parity
at review time.

## Why not run Jenkins in Docker locally?

It's tempting. Running `docker run jenkins/jenkins` would give us a real
Jenkins instance to point at this repo, and the Jenkinsfile would
actually execute.

Skipped because:

1. **No reviewer will spin it up.** The portfolio audience reads files;
   they don't deploy infrastructure to verify a candidate's work.
2. **It would add a real maintenance burden** (Jenkins controller, agent,
   plugin updates) for a project whose actual CI is already covered by
   GitHub Actions.
3. **The Jenkinsfile is more credible as a static artifact** in this
   context. Pretending Jenkins is running when it isn't would be
   dishonest framing; presenting the file openly as "this is what I'd
   write, GitHub Actions is what actually runs" is straightforward.

If this project ever moves into a real Jenkins shop, the existing
Jenkinsfile is a starting point that should run with minor adjustments
(webhook setup, credential bindings, agent labels).
