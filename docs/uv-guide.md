# UV Commands Cheat Sheet

## Add packages from requirements.txt

uv add --requirements requirements.txt

## Install dependencies from uv.lock

uv sync --frozen

## Update lockfile after changing pyproject.toml

uv lock

## Run the app

uv run python app/main.py

## Run tests

uv run pytest
