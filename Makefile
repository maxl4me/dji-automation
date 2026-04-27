.PHONY: install browsers test smoke allure allure-serve clean

install:
	pip install -e '.[dev]'

browsers:
	playwright install chromium

test:
	pytest

smoke:
	pytest -m smoke

allure:
	allure generate allure-results -o allure-report --clean

allure-serve:
	allure serve allure-results

clean:
	rm -rf allure-results allure-report playwright-traces .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
