// Jenkins declarative pipeline for the DJI Global automation suite.
//
// This file is the deliverable. There is no running Jenkins server pointed
// at this repo — this is a solo portfolio project, and operating a Jenkins
// instance would add cost and maintenance without adding signal. The real
// CI runs in GitHub Actions (see .github/workflows/tests.yml). This file
// demonstrates the same pipeline expressed in Jenkins's declarative DSL,
// which is what most enterprise QA shops actually use.
//
// What this pipeline does (mirrors GitHub Actions):
//   1. Check out the code (Jenkins does this implicitly for declarative pipelines)
//   2. Run inside a Python 3.12 Docker container (agent block)
//   3. Install the framework + dev dependencies
//   4. Install Playwright's Chromium binary and system libraries
//   5. Run pytest headless (DJI_BROWSER__HEADLESS=true)
//   6. Archive Allure results always
//   7. Archive Playwright traces only on failure
//
// What this pipeline does NOT do that the GHA equivalent does:
//   - Pip/Playwright cache: Jenkins agents are stateful by default, so the
//     workspace persists between builds on the same agent. We rely on that
//     instead of an explicit cache action. Inside a Docker agent the cache
//     is scoped to the container lifetime, so first-build cold-start cost
//     is paid every time. Accepted trade-off for a clean reproducible env.
//
// See docs/CI.md for a side-by-side comparison and the rationale.

pipeline {
    // Run every stage inside a Docker container based on the official
    // Playwright Python image. It ships with Python, Playwright, and all
    // the system libs Chromium needs preinstalled — so we skip the
    // apt-get dance and the playwright install-deps step.
    agent {
        docker {
            image 'mcr.microsoft.com/playwright/python:v1.58.0-jammy'
            // --ipc=host is the Playwright-recommended flag for Chromium
            // in Docker — without it, Chromium's shared memory can run
            // out and tabs crash. Documented at
            // https://playwright.dev/docs/docker
            args '--ipc=host'
        }
    }

    options {
        // Hard ceiling. The full suite runs in ~30s; 15 minutes is the
        // same cap GitHub Actions uses, kept for parity.
        timeout(time: 15, unit: 'MINUTES')
        // Keep the last 20 builds' logs and artifacts; older runs are
        // discarded to bound disk usage on the Jenkins controller.
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '20'))
        // Show timestamps next to every log line. Requires the
        // "Timestamper" plugin, which is in the recommended set.
        timestamps()
    }

    triggers {
        // Poll GitHub every 5 minutes for new commits on the watched branch.
        // The H is Jenkins's "hash" wildcard — it staggers the actual poll
        // time across jobs so the controller isn't hammered at exactly
        // HH:00, HH:05, HH:10. Spread the load.
        //
        // In a real shop you'd use a GitHub webhook instead of polling —
        // webhooks are push-based and react instantly. SCM polling is
        // shown here because it works without configuring GitHub to talk
        // to Jenkins, which a portfolio reviewer can verify just by
        // reading the file.
        pollSCM('H/5 * * * *')
    }

    environment {
        // Same env-var override mechanism as local and GitHub Actions.
        // config.ini stays unchanged; Jenkins forces headless at runtime.
        DJI_BROWSER__HEADLESS = 'true'
    }

    stages {
        stage('Install dependencies') {
            steps {
                sh '''
                    python -m pip install --upgrade pip
                    pip install -e '.[dev]'
                '''
            }
        }

        stage('Install Playwright browser') {
            steps {
                // The Playwright Docker image ships with browsers preinstalled,
                // but we run this anyway so the Jenkinsfile works if someone
                // swaps in a vanilla Python image. Idempotent: no-op on hit.
                sh 'playwright install chromium'
            }
        }

        stage('Run tests') {
            steps {
                // -v: verbose, one line per test.
                // --alluredir is already set in pyproject.toml addopts,
                // so we don't repeat it here.
                sh 'pytest -v'
            }
        }
    }

    post {
        // Runs after every build, regardless of outcome. Matches the
        // "if: always()" pattern in GitHub Actions.
        always {
            archiveArtifacts(
                artifacts: 'allure-results/**',
                allowEmptyArchive: true,
                fingerprint: false
            )
        }
        // Runs only when the build failed. Matches "if: failure()".
        failure {
            archiveArtifacts(
                artifacts: 'playwright-traces/**',
                allowEmptyArchive: true,
                fingerprint: false
            )
        }
        // Optional: clean the workspace between builds. Trade-off — losing
        // the workspace also loses the pip download cache. For a small
        // suite like this one the rebuild cost is negligible; cleaning
        // wins by avoiding "works on a dirty workspace" surprises.
        cleanup {
            cleanWs(
                deleteDirs: true,
                notFailBuild: true
            )
        }
    }
}
