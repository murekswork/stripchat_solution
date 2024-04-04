make lint:
	flake8 config
	isort config
	mypy config
	black config

make deps:
	pip-compile requirements/dev/requirements.in
	pip-compile requirements/lints/requirements.in
	pip-sync requirements/lints/requirements.txt requirements/dev/requirements.txt

make setup-playwright:
	playwright install --with-deps --force