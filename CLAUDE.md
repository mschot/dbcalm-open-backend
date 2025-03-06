# Backrest Project Guide

## Build & Run Commands
- Run server: `python main.py` or `cd dev && make dev`
- Lint: `ruff check .` or `ruff check . --fix`
- Tests: `.venv/bin/python -m pytest tests/`
- Pre-commit hook (runs automatically): Runs linter and tests
- Build command binary: `pyinstaller backrest-cmd.py`

## Code Style Guidelines
- Python 3.11+ required
- Use FastAPI framework conventions
- Linting: Ruff (`tool.ruff.lint` in pyproject.toml)
- Structure: Follow domain-driven design with modular components
- Imports: Group standard lib first, then third-party, then local
- Naming: snake_case for functions/variables, PascalCase for classes
- Error handling: Use appropriate exceptions with descriptive messages
- Type hints: Use throughout codebase
- Architecture pattern: Repository pattern with adapters
- Comments: Docstrings for public interfaces, TODOs with noqa: FIX002
- Use Path from pathlib instead of os operations where possible
- Use f-strings for string formatting
- Use double quotes for strings
- Use comma after last item in list/tuple/dict/set if multiline


## Project Organization
- `/backrest`: Core server code
- `/backrest_client`: Client library for interacting with the command Service tool via unix domain socket
- `/backrest-cmd.py`: Service tool entry point executing backups and restores
- `/backrest_cmd`: Command Service for interacting with mariabackup and mysqladmin