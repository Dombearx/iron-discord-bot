black:
	poetry run black ./src

flake:
	poetry run autoflake --quiet --in-place --recursive --ignore-init-module-imports --remove-unused-variables --remove-all-unused-imports ./src

isort:
	poetry run isort ./src

typehint_check:
	poetry run mypy --no-site-packages --ignore-missing-imports --no-strict-optional --explicit-package-bases ./src

format: flake typehint_check black

install:
	poetry install --no-root

run:
	poetry run python main.py
