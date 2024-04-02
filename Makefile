make lint:
	flake8 config
	isort config
	mypy config
	black config
